# app/routes/transacoes.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import List, Optional
from datetime import datetime

from app.db.repositories.transacao import TransacaoRepository
from app.schemas.transacao import TransacaoCreate, TransacaoResponse, TransacaoUpdate
from app.logger import log_api_request

router = APIRouter(prefix="/transacoes", tags=["Transações"])

@router.post("/", response_model=TransacaoResponse, status_code=status.HTTP_201_CREATED)
async def create_transacao(
    request: Request,
    payload: TransacaoCreate,
    status_code=status.HTTP_201_CREATED,
    repo: TransacaoRepository = Depends()
):
    """
    Cria uma transação. Se categoria/subcategoria não existirem, são criadas.
    """
    log = log_api_request(method="POST", endpoint=str(request.url), payload=payload.model_dump())
    try:
        return await repo.create(payload)
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erro interno ao criar transação: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")



@router.get(
    "/",
    response_model=List[TransacaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar transações",
    description="Lista todas as transações, com filtros opcionais por data."
)
async def list_transacoes(
    request: Request,
    data_inicio: Optional[datetime] = Query(None),
    data_final: Optional[datetime] = Query(None),
    repo: TransacaoRepository = Depends(TransacaoRepository)
):
    """
    Obtém transações entre data_inicio e data_final, se fornecidas.
    """
    log = log_api_request(
        method="GET",
        endpoint=str(request.url),
        data_inicio=data_inicio,
        data_final=data_final
    )
    try:
        transacoes = await repo.get_all(data_inicio, data_final)
        log.info(f"{len(transacoes)} transações listadas")
        return transacoes
    except Exception as e:
        log.error(f"Erro ao listar transações: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar transações"
        )


@router.get(
    "/{transacao_id}",
    response_model=TransacaoResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter transação por ID",
    description="Retorna detalhes de uma transação específica."
)
async def get_transacao_by_id(
    request: Request,
    transacao_id: int,
    repo: TransacaoRepository = Depends(TransacaoRepository)
):
    """
    Busca transação pelo seu identificador.
    """
    log = log_api_request(method="GET", endpoint=str(request.url), transacao_id=transacao_id)
    trans = await repo.get_by_id(transacao_id)
    if not trans:
        log.warning(f"Transação {transacao_id} não encontrada")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada"
        )
    log.info(f"Transação {transacao_id} retornada")
    return trans


@router.put(
    "/{transacao_id}",
    response_model=TransacaoResponse,
    summary="Atualizar transação",
)
async def update_transacao(
    request: Request,
    transacao_id: int,
    payload: TransacaoUpdate,
    repo: TransacaoRepository = Depends(TransacaoRepository)
):
    log = log_api_request(method="PUT", endpoint=str(request.url), transacao_id=transacao_id, payload=payload.dict(exclude_unset=True))
    trans = await repo.update(transacao_id, payload)
    if not trans:
        log.warning(f"Transação {transacao_id} não encontrada")
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    log.info(f"Transação {transacao_id} atualizada")
    return trans



@router.delete(
    "/{transacao_id}",
    response_model=TransacaoResponse,
    summary="Excluir transação",
    description="Remove uma transação pelo seu ID."
)
async def delete_transacao(
    request: Request,
    transacao_id: int,
    repo: TransacaoRepository = Depends(TransacaoRepository)
):
    """
    Exclui uma transação existente.
    """
    log = log_api_request(method="DELETE", endpoint=str(request.url), transacao_id=transacao_id)
    try:
        deleted = await repo.delete(transacao_id)
        if not deleted:
            log.warning(f"Tentativa de excluir transação {transacao_id} não encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )
        log.info(f"Transação {transacao_id} excluída")
        return deleted
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erro ao excluir transação {transacao_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao excluir transação"
        )
