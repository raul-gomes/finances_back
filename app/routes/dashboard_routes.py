import calendar
from fastapi import APIRouter, Query, Depends, HTTPException, status
from typing import Any, Dict, Literal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

from app.db.repositories.dashboard import DashboardRepository
from app.schemas.dashboard import EntradasPorCategoriaResponse, ExtratoResponse, GastosPorCategoriaResponse, OpcoesCategoriaResponse, RendimentoPeriodoResponse

from app.logger import log_api_request



router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def parse_date(date_str: str, field_name: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Formato inválido para {field_name}. Use DD/MM/YYYY.")

@router.get(
    "/extrato",
    response_model=ExtratoResponse,
    summary="Extrato financeiro completo",
    description="Retorna entradas, saídas, meta e lista de transações no período",
    status_code=status.HTTP_200_OK
)
async def extrato_financeiro(
    data_inicio: str = Query(..., description="Data inicial DD/MM/YYYY"),
    data_final: str = Query(..., description="Data final DD/MM/YYYY"),
    natureza: str = Query(..., description="Natureza jurídica: pf ou pj"),
    db: AsyncSession = Depends(get_session)
):
    api_logger = log_api_request("GET", "/dashboard/extrato")

    dt_i = parse_date(data_inicio, "data_inicio")
    dt_f = parse_date(data_final, "data_final")
    dt_f = datetime.combine(dt_f.date(), datetime.max.time())

    dashboard_repo = DashboardRepository(db)
    extrato = await dashboard_repo.extrato_financeiro(dt_i, dt_f, natureza, data_inicio, data_final)

    api_logger.success(
        "Extrato gerado", 
        entradas=extrato.entradas, 
        saidas=extrato.saidas, 
        count=len(extrato.transacoes)
    )

    return extrato



@router.get(
    "/rendimento-periodo",
    response_model=RendimentoPeriodoResponse,
    summary="Rendimento por período",
    description="Retorna entradas/saídas agregadas por mês no ano"
)
async def rendimento_periodo(
    ano: int = Query(..., description="Ano para agregação (YYYY)"),
    natureza: str = Query(..., description="Natureza jurídica: pf ou pj"),
    db: AsyncSession = Depends(get_session)
):
    api_logger = log_api_request("GET", "/dashboard/rendimento-periodo")

    dashboard_repo = DashboardRepository(db)
    rendimento_ano = await dashboard_repo.rendimento_por_periodo(ano, natureza)

    api_logger.success("Rendimento por período gerado", year=ano)

    return rendimento_ano

@router.get(
    "/gastos-por-categoria",
    response_model=GastosPorCategoriaResponse,
    summary="Gastos por subcategoria",
    description="Retorna gastos por categoria/subcategoria incluindo limite"
)
async def gastos_por_categoria(
    data_inicio: str = Query(..., description="Data inicial DD/MM/YYYY"),
    data_final: str = Query(..., description="Data final DD/MM/YYYY"),
    natureza: str = Query(..., description="Natureza jurídica: pf ou pj"),
    db: AsyncSession = Depends(get_session),
):
    dt_i = datetime.strptime(data_inicio, "%d/%m/%Y")
    dt_f = datetime.strptime(data_final, "%d/%m/%Y")
    dt_f = datetime.combine(dt_f.date(), datetime.max.time())

    dashboard_repo = DashboardRepository(db)
    categorias = await dashboard_repo.gastos_por_categoria(dt_i, dt_f, natureza)
    
    return GastosPorCategoriaResponse(
        data_inicial=data_inicio,
        data_final=data_final,
        categorias=categorias
    )

@router.get(
    '/opcoes-categorias',
    response_model=OpcoesCategoriaResponse,
    summary='Opções de categorias e subcategorias',
    description='Retorna lista de categorias com suas respectivas subcategorias.'
)
async def opcoes_categorias(
    natureza: Literal['pf', 'pj', 'all'] = Query('all'),
    db: AsyncSession = Depends(get_session)
) -> OpcoesCategoriaResponse:
    
    api_logger = log_api_request('GET', '/dashboard/opcoes-categorias', natureza=natureza)
    api_logger.info('Gerando opções de categorias', natureza=natureza)

    dashboard_repo = DashboardRepository(db)
    opcoes = await dashboard_repo.opcoes_categorias(natureza)

    api_logger.success('Opções de categorias retornadas', count=len(opcoes.opcoes))
    return opcoes

@router.get(
    '/entradas-por-categoria',
    response_model=EntradasPorCategoriaResponse,
    summary='Entradas por subcategoria',
    description='Retorna valores de entradas por subcategoria agrupados por categoria'
)
async def entradas_por_categoria(
    data_inicio: str = Query(..., description='Data inicial DD/MM/YYYY'),
    data_final: str = Query(..., description='Data final DD/MM/YYYY'),
    natureza: str = Query(..., description='Natureza jurídica: pf ou pj'),
    db: AsyncSession = Depends(get_session)
):
    api_logger = log_api_request('GET', '/dashboard/entradas-por-categoria')
    
    dt_i = parse_date(data_inicio, 'data_inicio')
    dt_f = parse_date(data_final, 'data_final')
    dt_f = datetime.combine(dt_f.date(), datetime.max.time())

    dashboard_repo = DashboardRepository(db)
    resultado = await dashboard_repo.entradas_por_categoria(dt_i, dt_f, natureza, data_inicio, data_final)

    api_logger.success('Entradas por categoria geradas', count=len(resultado.subcategorias))
    return resultado
