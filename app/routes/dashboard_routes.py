# # app/routes/dashboard_full.py

# from fastapi import APIRouter, HTTPException, Depends, status, Query
# from typing import List, Dict, Any, Literal
# from datetime import datetime, timedelta
# import calendar

# from app.core.database import get_database
# from app.logger import log_api_request
# from app.models.transacoes_model import TransacaoResponse
# from app.routes.categorias_routes import get_categorias_collection
# from ..models.categorias_model import Categoria

# router = APIRouter(prefix='/dashboard', tags=['Dashboard'])

# def parse_date(s: str, name: str) -> datetime:
#     try:
#         return datetime.strptime(s, '%d/%m/%Y')
#     except ValueError:
#         raise HTTPException(status.HTTP_400_BAD_REQUEST, f'{name} deve estar no formato DD/MM/YYYY')


# @router.get(
#     '/extrato',
#     response_model=Dict[str, Any],
#     summary='Extrato financeiro completo',
#     description='Retorna entradas, saídas, meta e lista de transações no período'
# )
# async def extrato_financeiro(
#     data_inicio: str = Query(..., description='Data inicial DD/MM/YYYY'),
#     data_final: str  = Query(..., description='Data final   DD/MM/YYYY'),
#     natureza: str    = Query(..., description='Natureza jurídica: pf ou pj'),
#     db=Depends(get_database)
# ):
#     api_logger = log_api_request('GET', '/dashboard/extrato')
#     dt_i = parse_date(data_inicio, 'data_inicio')
#     dt_f = parse_date(data_final,   'data_final')
#     dt_f = datetime.combine(dt_f.date(), datetime.max.time())

#     trans = db.transacoes
#     match_filter = {
#         'data_transacao': {'$gte': dt_i, '$lte': dt_f},
#         'natureza_transacao': natureza
#     }

#     pipeline = [
#         {'$match': match_filter},
#         {'$group': {'_id':'$tipo', 'total':{'$sum':'$valor'}}}
#     ]
#     agg = await trans.aggregate(pipeline).to_list(None)
#     entradas = next((a['total'] for a in agg if a['_id']=='entrada'), 0.0)
#     saidas   = next((a['total'] for a in agg if a['_id']=='saida'),   0.0)

#     docs = await trans.find(match_filter).sort('data_transacao', -1).to_list(None)
#     txs = [TransacaoResponse(**{**d, 'id': str(d['_id'])}) for d in docs]

#     meta_mensal = 4000.0
#     api_logger.success('Extrato gerado', entradas=entradas, saidas=saidas, count=len(txs))
#     return {
#         'entradas': entradas,
#         'saidas':   saidas,
#         'data_inicial': data_inicio,
#         'data_final':   data_final,
#         'meta_mensal':  meta_mensal,
#         'total_investido': entradas,
#         'transações': txs
#     }


# @router.get(
#     '/rendimento-periodo',
#     response_model=Dict[str, Any],
#     summary='Rendimento por período',
#     description='Retorna entradas/saídas agregadas por mês no ano'
# )
# async def rendimento_periodo(
#     ano: int      = Query(..., description='Ano para agregação (YYYY)'),
#     natureza: str = Query(..., description='Natureza jurídica: pf ou pj'),
#     db=Depends(get_database)
# ):
#     api_logger = log_api_request('GET', '/dashboard/rendimento-periodo')
#     trans = db.transacoes
#     meses_data: Dict[str, Dict[str, float]] = {}

#     for m in range(1, 13):
#         first = datetime(ano, m, 1)
#         last_day = calendar.monthrange(ano, m)[1]
#         last = datetime(ano, m, last_day, 23, 59, 59)

#         pipeline = [
#             {'$match': {
#                 'data_transacao': {'$gte': first, '$lte': last},
#                 'natureza_transacao': natureza
#             }},
#             {'$group': {'_id':'$tipo', 'total':{'$sum':'$valor'}}}
#         ]
#         agg = await trans.aggregate(pipeline).to_list(None)
#         ent = next((a['total'] for a in agg if a['_id']=='entrada'), 0.0)
#         sai = next((a['total'] for a in agg if a['_id']=='saida'),   0.0)
#         meses_data[calendar.month_name[m].lower()] = {
#             'entrada': round(ent, 2),
#             'saida':   round(sai, 2)
#         }

#     limite = 4000.0
#     api_logger.success('Rendimento por período gerado', year=ano)
#     return {'limite': limite, 'meses': [meses_data]}


# @router.get(
#     '/opcoes-transacao',
#     response_model=Dict[str, List[str]],
#     summary='Mapa de categoria → subcategorias',
#     description='Retorna mapeamento categoria → lista de nomes de subcategorias.'
# )
# async def opcoes_transacao(
#     natureza: Literal['pf','pj','all'] = Query('all'),
#     collection=Depends(get_categorias_collection)
# ) -> Dict[str, List[str]]:
#     api_logger = log_api_request('GET', '/dashboard/opcoes-transacao', natureza=natureza)
#     api_logger.info('Gerando opções de transação', natureza=natureza)

#     # Filtra pelo campo natureza se não for 'all'
#     filtro = {} if natureza == 'all' else {'natureza': natureza}
#     docs = await collection.find(filtro).to_list(None)

#     # Constrói dict categoria → lista de subcategorias como strings
#     opcoes: Dict[str, List[str]] = {}
#     for doc in docs:
#         nome = doc['categoria_nome']
#         subs = doc.get('subcategorias', [])
#         # Cada sub é um dict {"subcategoria_nome": ...}
#         opcoes[nome] = [s['subcategoria_nome'] for s in subs]

#     api_logger.success('Opções retornadas', count=len(opcoes))
#     return opcoes


# @router.get(
#     '/gastos-por-categoria',
#     response_model=Dict[str, Any],
#     summary='Gastos por subcategoria',
#     description='Retorna gastos por categoria/subcategoria incluindo limite'
# )
# async def gastos_por_categoria(
#     data_inicio: str = Query(..., description='Data inicial DD/MM/YYYY'),
#     data_final: str  = Query(..., description='Data final   DD/MM/YYYY'),
#     natureza: str   = Query(..., description='Natureza jurídica: pf ou pj'),
#     db=Depends(get_database)
# ):
#     api_logger = log_api_request('GET', '/dashboard/gastos-por-categoria')
#     api_logger.info(f'Requisição recebida: data_inicio={data_inicio}, data_final={data_final}, natureza={natureza}')
    
#     dt_i = parse_date(data_inicio,'data_inicio')
#     dt_f = parse_date(data_final,'data_final')
#     dt_f = datetime.combine(dt_f.date(), datetime.max.time())
#     trans = db.transacoes
#     categorias_collection = db.categorias
    
#     try:
#         pipeline = [
#             {
#                 '$match': {
#                     'data_transacao': {'$gte': dt_i, '$lte': dt_f},
#                     'natureza_transacao': natureza,
#                     'tipo': 'saida',
#                 }
#             },
#             {
#                 '$group': {
#                     '_id': {
#                         'categoria': '$categoria',
#                         'subcategoria': '$subcategoria',
#                     },
#                     'total_sub': {'$sum': '$valor'}
#                 }
#             },
#             {
#                 '$group': {
#                     '_id': '$_id.categoria',
#                     'total_categoria': {'$sum': '$total_sub'},
#                     'subcategorias': {
#                         '$push': {
#                             'nome': '$_id.subcategoria',
#                             'valor': {'$toString': {'$round': ['$total_sub', 2]}}
#                         }
#                     }
#                 }
#             }
#         ]
#         api_logger.info('Executando agregação no MongoDB')
#         resultados = await trans.aggregate(pipeline).to_list(None)
#         api_logger.info(f'Agregação retornou {len(resultados)} resultados')

#         cats = await categorias_collection.find().to_list(None)
#         cats_map = {c['categoria_nome']: c.get('limite', 0.0) for c in cats}
#         api_logger.info(f'Carregadas {len(cats_map)} categorias com limites')

#         output = []
#         nomes_resultados = set()

#         for r in resultados:
#             nome_cat = r['_id']
#             nomes_resultados.add(nome_cat)
#             output.append({
#                 'nome': nome_cat,
#                 'total': round(r['total_categoria'], 2),
#                 'limite': cats_map.get(nome_cat, 0.0),
#                 'subcategorias': r['subcategorias']
#             })

#         # Inclui categorias sem transações
#         for c_nome, limite in cats_map.items():
#             if c_nome not in nomes_resultados:
#                 api_logger.info(f'Inclusão de categoria sem transações: {c_nome}')
#                 output.append({
#                     'nome': c_nome,
#                     'total': 0,
#                     'limite': limite,
#                     'subcategorias': []
#                 })

#         extras = [
#             {'total': 0, 'limite': 0, 'nome': 'salário', 'subcategorias': []},
#             {'total': 0, 'limite': 0, 'nome': 'reembolso', 'subcategorias': []},
#         ]
#         output.extend(extras)
#         api_logger.info(f'Categorias extras adicionadas: {len(extras)}')

#         api_logger.success('Gastos por categoria gerados via agregação', count=len(output))
#         return {
#             'data_inicial': data_inicio,
#             'data_final': data_final,
#             'categorias': output
#         }
#     except Exception as e:
#         api_logger.error(f'Erro ao gerar gastos por categoria: {str(e)}')
#         raise


# @router.get(
#     '/entradas-por-categoria',
#     response_model=Dict[str, Any],
#     summary='Entradas por subcategoria',
#     description='Retorna valores de entradas por subcategoria agrupados por categoria'
# )
# async def entradas_por_categoria(
#     data_inicio: str = Query(..., description='Data inicial DD/MM/YYYY'),
#     data_final: str  = Query(..., description='Data final   DD/MM/YYYY'),
#     natureza: str    = Query(..., description='Natureza jurídica: pf ou pj'),
#     db=Depends(get_database)
# ):
#     api_logger = log_api_request('GET', '/dashboard/entradas-por-categoria')
#     dt_i = parse_date(data_inicio,'data_inicio')
#     dt_f = parse_date(data_final,'data_final')
#     dt_f = datetime.combine(dt_f.date(), datetime.max.time())
#     trans = db.transacoes

#     cats = await db.categorias.find().to_list(None)
#     output: List[Dict[str, Any]] = []
#     for c in cats:
#         filtro = {
#             'data_transacao': {'$gte': dt_i, '$lte': dt_f},
#             'natureza_transacao': natureza,
#             'categoria': c['categoria_nome'],
#             'tipo': 'entrada'
#         }
#         docs = await trans.find(filtro).to_list(None)
#         subs: Dict[str, float] = {}
#         total = 0.0
#         for d in docs:
#             val = d['valor']
#             total += val
#             subs.setdefault(d['subcategoria'], 0.0)
#             subs[d['subcategoria']] += val
#         output.append({
#             'total': round(total, 2),
#             c['categoria_nome'].lower(): {k: round(v, 2) for k, v in subs.items()}
#         })

#     api_logger.success('Entradas por categoria geradas', count=len(output))
#     return {
#         'data_inicial': data_inicio,
#         'data_final':   data_final,
#         'subcategorias': output
#     }
