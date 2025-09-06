from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.db.repositories.categoria import CategoriaRepository
from app.schemas.categorias import Categoria
from app.schemas.transacao import TransacaoCreate, TransacaoResponse
from app.db.repositories.transacao import TransacaoRepository
from typing import List


router = APIRouter(prefix='/categorias', tags=['Categorias'])

@router.get('/',
           response_model=List[Categoria],
           status_code=status.HTTP_200_OK)
async def list_categoria(
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    categorias = await repo.get_all()
    return categorias

# @router.post(
#     '/',
#     response_model=TransacaoResponse,
#     status_code=status.HTTP_201_CREATED
#     )
# async def create_transcao(
#     payload: TransacaoCreate,
#     repo: TransacaoRepository = Depends(TransacaoRepository)
# ):
#     return await repo.create(payload)