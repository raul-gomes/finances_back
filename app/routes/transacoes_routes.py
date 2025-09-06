from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.transacao import TransacaoCreate, TransacaoResponse
from app.db.repositories.transacao import TransacaoRepository
from typing import Optional


router = APIRouter(prefix='/categorias', tags=['Categorias'])


@router.get(
        '/',
        response_model=TransacaoResponse,
        status_code=status.HTTP_200_OK)
async def get_all(
    data_inicio: Optional[datetime] = Query(..., description='Data inicial'),
    data_final: Optional[datetime] = Query(..., description='Data Final'),
    repo: TransacaoRepository = Depends(TransacaoRepository)
):
    print(data_inicio)
    print(data_final)
    dt_inicio = datetime.combine(data_inicio, datetime.min.time()) if data_inicio else None
    dt_fim = datetime.combine(data_final, datetime.max.time()) if data_final else None
    print(dt_inicio, dt_fim)
    
    return await repo.get_all(
        data_inicio=dt_inicio,
        data_final=dt_fim
    )

@router.post(
    '/',
    response_model=TransacaoResponse,
    status_code=status.HTTP_201_CREATED
    )
async def create_transacao(
    payload: TransacaoCreate,
    repo: TransacaoRepository = Depends(TransacaoRepository)
):
    return await repo.create(payload)