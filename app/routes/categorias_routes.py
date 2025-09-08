from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List

from app.db.repositories.categoria import CategoriaRepository
from app.schemas.categorias import Categoria, CategoriaCreate, CategoriaUpdate
from app.logger import log_api_request

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get(
    "/",
    response_model=List[Categoria],
    status_code=status.HTTP_200_OK,
    summary="Listar todas as categorias",
    description="Retorna todas as categorias com suas subcategorias."
)
async def list_categoria(
    request: Request,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    """
    Obtém a lista completa de categorias.
    """
    log = log_api_request(method="GET", endpoint=str(request.url))
    try:
        categorias = await repo.get_all()
        log.info("Categorias listadas com sucesso")
        return categorias
    except Exception as e:
        log.error(f"Erro ao listar categorias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar categorias"
        )


@router.get(
    "/{categoria_id}",
    response_model=Categoria,
    status_code=status.HTTP_200_OK,
    summary="Obter categoria por ID",
    description="Retorna a categoria com o ID informado."
)
async def get_categoria_by_id(
    request: Request,
    categoria_id: int,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    """
    Busca uma categoria pelo seu identificador.
    """
    log = log_api_request(method="GET", endpoint=str(request.url), categoria_id=categoria_id)
    categoria = await repo.get_by_id(categoria_id)
    if not categoria:
        log.warning(f"Categoria {categoria_id} não encontrada")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )
    log.info(f"Categoria {categoria_id} retornada com sucesso")
    return categoria


@router.post(
    "/",
    response_model=Categoria,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova categoria",
    description="Cria uma nova categoria com eventuais subcategorias."
)
async def create_categoria(
    request: Request,
    payload: CategoriaCreate,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    """
    Cria uma categoria a partir dos dados fornecidos.
    """
    log = log_api_request(method="POST", endpoint=str(request.url), payload=payload.dict())
    try:
        categoria = await repo.create(payload)
        log.info(f"Categoria criada com ID {categoria.id}")
        return categoria
    except HTTPException:
        # já está logado e formatado no repositório
        raise
    except Exception as e:
        log.error(f"Erro ao criar categoria: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar categoria"
        )


@router.put(
    "/{categoria_id}",
    response_model=Categoria,
    summary="Atualizar categoria",
    description="Atualiza dados de categoria e suas subcategorias."
)
async def update_categoria(
    request: Request,
    categoria_id: int,
    payload: CategoriaUpdate,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    """
    Atualiza uma categoria existente e sincroniza subcategorias.
    """
    log = log_api_request(
        method="PUT", endpoint=str(request.url),
        categoria_id=categoria_id, payload=payload.dict(exclude_unset=True)
    )
    try:
        categoria = await repo.update(categoria_id, payload)
        if not categoria:
            log.warning(f"Tentativa de atualizar categoria {categoria_id} não encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada"
            )
        log.info(f"Categoria {categoria_id} atualizada com sucesso")
        return categoria
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erro ao atualizar categoria {categoria_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar categoria"
        )


@router.delete(
    "/{categoria_id}",
    response_model=Categoria,
    summary="Excluir categoria",
    description="Remove uma categoria pelo seu ID."
)
async def delete_categoria(
    request: Request,
    categoria_id: int,
    repo: CategoriaRepository = Depends(CategoriaRepository)
):
    """
    Deleta uma categoria existente.
    """
    log = log_api_request(method="DELETE", endpoint=str(request.url), categoria_id=categoria_id)
    try:
        categoria = await repo.delete(categoria_id)
        if not categoria:
            log.warning(f"Tentativa de excluir categoria {categoria_id} não encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada"
            )
        log.info(f"Categoria {categoria_id} excluída com sucesso")
        return categoria
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erro ao excluir categoria {categoria_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao excluir categoria"
        )
