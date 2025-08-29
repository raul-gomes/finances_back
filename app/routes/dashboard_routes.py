# app/routes/dashboard_full.py

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta
from calendar import month_name
from bson import ObjectId

from app.database import get_database
from app.logger import log_api_request
from app.models.transacoes_model import TransacaoResponse
from ..models.categorias_model import Categoria

router = APIRouter(prefix='/dashboard', tags=['Dashboard'])


def parse_date(s: str, name: str) -> datetime:
    try:
        return datetime.strptime(s, '%d/%m/%Y')
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f'{name} deve estar no formato DD/MM/YYYY')


@router.get(
    '/extrato',
    response_model=Dict[str, Any],
    summary='Extrato financeiro completo',
    description='Retorna entradas, saídas, meta e lista de transações no período'
)
async def extrato_financeiro(
    data_inicio: str = Query(..., description='Data inicial DD/MM/YYYY'),
    data_final: str  = Query(..., description='Data final   DD/MM/YYYY'),
    db=Depends(get_database)
):
    """
    Retorna:
    {
      entradas, saidas, data_inicial, data_final, meta_mensal,
      total_investido, transações: [TransacaoResponse…]
    }
    """
    api_logger = log_api_request('GET', '/dashboard/extrato')
    dt_i = parse_date(data_inicio, 'data_inicio')
    dt_f = parse_date(data_final,  'data_final')
    dt_f = datetime.combine(dt_f.date(), datetime.max.time())

    trans = db.transacoes
    # agregados
    pipeline = [
        {'$match': {'data_transacao': {'$gte': dt_i, '$lte': dt_f}}},
        {'$group': {'_id': '$tipo', 'total': {'$sum': '$valor'}}}
    ]
    agg = await trans.aggregate(pipeline).to_list(None)
    entradas = next((a['total'] for a in agg if a['_id']=='entrada'), 0.0)
    saidas   = next((a['total'] for a in agg if a['_id']=='saida'),   0.0)

    # transações detalhadas
    docs = await trans.find({'data_transacao': {'$gte': dt_i, '$lte': dt_f}})\
                      .sort('data_transacao', -1).to_list(None)
    txs = []
    for d in docs:
        d['id'] = str(d.pop('_id'))
        txs.append(TransacaoResponse(**d))

    # meta mensal da categoria geral (exemplo fixo)
    meta_mensal = 4000.0

    api_logger.success('Extrato gerado', entradas=entradas, saidas=saidas, count=len(txs))
    return {
        'entradas': round(entradas,2),
        'saidas':   round(saidas,2),
        'data_inicial': data_inicio,
        'data_final':   data_final,
        'meta_mensal':  meta_mensal,
        'total_investido': round(entradas,2),
        'transações': txs
    }


@router.get(
    '/rendimento-periodo',
    response_model=Dict[str, Any],
    summary='Rendimento por período',
    description='Retorna entradas/saídas agregadas por mês no ano'
)
async def rendimento_periodo(
    ano: int = Query(..., description='Ano para agregação (YYYY)'),
    db=Depends(get_database)
):
    """
    Retorna:
    {
      limite: float,
      meses: [
        {
          "janeiro":  {entrada, saida},
          …,
          "dezembro":{entrada, saida}
        }
      ]
    }
    """
    api_logger = log_api_request('GET', '/dashboard/rendimento-periodo')
    trans = db.transacoes
    meses_data = {}
    for m in range(1,13):
        first = datetime(ano, m, 1)
        last  = datetime(ano, m, 28,23,59,59)
        agg = await trans.aggregate([
            {'$match': {'data_transacao': {'$gte': first, '$lte': last}}},
            {'$group': {'_id':'$tipo', 'total':{'$sum':'$valor'}}}
        ]).to_list(None)
        ent = next((a['total'] for a in agg if a['_id']=='entrada'),0.0)
        sai = next((a['total'] for a in agg if a['_id']=='saida'),0.0)
        meses_data[month_name[m].lower()] = {'entrada':round(ent,2),'saida':round(sai,2)}

    limite = 123.12
    api_logger.success('Rendimento por período gerado', year=ano)
    return {'limite':limite, 'meses':[meses_data]}


@router.get(
    '/opcoes-transacao',
    response_model=Dict[str, List[str]],
    summary='Opções de categoria/subcategoria',
    description='Retorna mapa categoria→lista de subcategorias'
)
async def opcoes_transacao(
    db=Depends(get_database)
):
    """
    Retorna:
    {
      Categoria1:[sub1,sub2],
      Categoria2:[…],
      …
    }
    """
    api_logger = log_api_request('GET', '/dashboard/opcoes-transacao')
    docs = await db.categorias.find().to_list(None)
    result = {d['categoria_nome']: d.get('subcategorias',[]) for d in docs}
    api_logger.success('Opções retornadas', count=len(result))
    return result


@router.get(
    '/gastos-por-categoria',
    response_model=Dict[str, Any],
    summary='Gastos por subcategoria',
    description='Retorna gastos (apenas saídas) por subcategoria agrupados por categoria, incluindo limite.'
)
async def gastos_por_categoria(
    data_inicio: str = Query(..., description='Data inicial DD/MM/YYYY'),
    data_final: str  = Query(..., description='Data final   DD/MM/YYYY'),
    db=Depends(get_database)
):
    """
    Retorna:
    {
      data_inicial, data_final,
      subcategorias:[
        {
          total:float,
          limite:float,
          categoria1:{sub1:val,sub2:val,…}
        },…
      ]
    }
    Filtra apenas transações de tipo 'saida'.
    """
    api_logger = log_api_request('GET', '/dashboard/gastos-por-categoria')
    dt_i = parse_date(data_inicio,'data_inicio')
    dt_f = parse_date(data_final,'data_final')
    dt_f = datetime.combine(dt_f.date(), datetime.max.time())
    trans = db.transacoes

    cats = await db.categorias.find().to_list(None)
    output: List[Dict[str, Any]] = []
    for c in cats:
        filtro = {
            'data_transacao': {'$gte': dt_i, '$lte': dt_f},
            'categoria': c['categoria_nome'],
            'tipo': 'saida'
        }
        docs = await trans.find(filtro).to_list(None)
        subs: Dict[str, float] = {}
        total = 0.0
        for d in docs:
            val = d['valor']
            total += val
            subs.setdefault(d['subcategoria'], 0.0)
            subs[d['subcategoria']] += val
        output.append({
            'total': round(total, 2),
            'limite': c.get('limite', 0.0),
            c['categoria_nome'].lower(): {k: round(v, 2) for k, v in subs.items()}
        })
    api_logger.success('Gastos por categoria gerados', count=len(output))
    return {
        'data_inicial': data_inicio,
        'data_final': data_final,
        'subcategorias': output
    }

@router.get(
    '/entradas-por-categoria',
    response_model=Dict[str, Any],
    summary='Entradas por subcategoria',
    description='Retorna valores de entradas por subcategoria agrupados por categoria'
)
async def entradas_por_categoria(
    data_inicio: str = Query(..., description='Data inicial DD/MM/YYYY'),
    data_final: str  = Query(..., description='Data final   DD/MM/YYYY'),
    db=Depends(get_database)
):
    """
    Retorna:
    {
      data_inicial, data_final,
      subcategorias:[
        {
          total:float,
          categoria1:{sub1:val,sub2:val,…}
        },…
      ]
    }
    Filtra apenas transações de tipo 'entrada'.
    """
    api_logger = log_api_request('GET', '/dashboard/entradas-por-categoria')
    dt_i = parse_date(data_inicio,'data_inicio')
    dt_f = parse_date(data_final,'data_final')
    dt_f = datetime.combine(dt_f.date(), datetime.max.time())
    trans = db.transacoes

    cats = await db.categorias.find().to_list(None)
    output: List[Dict[str, Any]] = []
    for c in cats:
        filtro = {
            'data_transacao': {'$gte': dt_i, '$lte': dt_f},
            'categoria': c['categoria_nome'],
            'tipo': 'entrada'
        }
        docs = await trans.find(filtro).to_list(None)
        subs: Dict[str, float] = {}
        total = 0.0
        for d in docs:
            val = d['valor']
            total += val
            subs.setdefault(d['subcategoria'], 0.0)
            subs[d['subcategoria']] += val
        output.append({
            'total': round(total, 2),
            c['categoria_nome'].lower(): {k: round(v, 2) for k, v in subs.items()}
        })
    api_logger.success('Entradas por categoria geradas', count=len(output))
    return {
        'data_inicial': data_inicio,
        'data_final': data_final,
        'subcategorias': output
    }
