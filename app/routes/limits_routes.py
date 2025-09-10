# app/routes/limits.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.database import get_session
from app.db.repositories.limits import LimitsRepository
from app.schemas.limits import LimitsUpdatePayload, LimitsUpdateResponse

router = APIRouter(prefix="/limits", tags=["Limits"])


@router.get(
    "/",
    response_model=List[Dict[str, Any]],
    summary="Listar todas as categorias e limites",
    description="Retorna todas as categorias com subcategorias formatadas para gestão de limites"
)
async def get_all_limits(
    db: AsyncSession = Depends(get_session)
):
    """
    Endpoint para buscar todas as categorias e subcategorias para gestão de limites.
    """
    limits_repo = LimitsRepository(db)
    return await limits_repo.get_all_limits()


@router.put(
    "/",
    response_model=LimitsUpdateResponse,
    summary="Atualizar limites em lote",
    description="Processa atualizações em lote de categorias e subcategorias, criando novas e atualizando existentes",
    status_code=status.HTTP_200_OK
)
async def update_limits_bulk(
    payload: LimitsUpdatePayload,
    db: AsyncSession = Depends(get_session)
):
    """
    Endpoint para atualização em lote de limites.
    
    Processa duas listas:
    - `new`: Categorias novas (sem ID) que serão criadas
    - `modified`: Categorias existentes (com ID) que serão atualizadas
    
    Exemplo de payload:
    ```json
    {
        "new": [
            {
                "categoria_nome": "Nova Categoria",
                "natureza": "pf",
                "limite": 1000,
                "subcategorias": [
                    {"subcategoria_nome": "Nova Sub"}
                ]
            }
        ],
        "modified": [
            {
                "id": 2,
                "categoria_nome": "Categoria Modificada",
                "natureza": "pf", 
                "limite": 1500,
                "subcategorias": [
                    {"id": 3, "subcategoria_nome": "Sub Existente"},
                    {"subcategoria_nome": "Sub Nova"}
                ]
            }
        ]
    }
    ```
    """
    limits_repo = LimitsRepository(db)
    return await limits_repo.bulk_update_limits(payload)