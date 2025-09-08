from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.db.repositories.categoria import CategoriaRepository
from app.schemas.categorias import Categoria, CategoriaCreate, CategoriaUpdate
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

@router.get('/{categoria_id}',
            response_model=Categoria,
            status_code=status.HTTP_200_OK)
async def get_categoria_by_id(
    categoria_id: int,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    categoria = await repo.get_by_id(categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Categoria não encotnrada'
        )
    return categoria

@router.post(
    '/',
    response_model=Categoria,
    status_code=status.HTTP_201_CREATED
    )
async def create_transcao(
    payload: CategoriaCreate,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    categoria = await repo.create(payload)
    return categoria



@router.put(
    '/{categoria_id}',
    response_model=Categoria
)
async def update_categoria(
    categoria_id: int,
    payload: CategoriaUpdate,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    categoria = await repo.update(categoria_id, payload)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Categoria não encontrada'
        )
    return categoria

@router.delete(
    '/{categoria_id}',
    response_model=Categoria
)
async def delete_categoria(
    categoria_id: int,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    categoria = await repo.delete(categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Categoria não encontrada'
        )
    return categoria