import traceback
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from datetime import datetime
from app.core.database import get_database
from app.models.limits_model import LimitsResponse
from app.logger import log_api_request

router = APIRouter(prefix="/limits", tags=["Limits"])

def get_database_limites():
    return get_database().categorias

@router.put("/", response_model=LimitsResponse)
async def upsert_limits(
    payload: LimitsResponse,
    background_tasks: BackgroundTasks,
    db=Depends(get_database_limites),
) -> LimitsResponse:
    api_logger = log_api_request("PUT", "/limits")
    try:
        api_logger.debug(f"Received payload: {payload!r}")
        new_groups = payload.model_dump()
        now = datetime.utcnow()

        categorias_coll = get_database().categorias
        transacoes_coll = get_database().transacoes

        # 1. Busca todas as categorias antigas (antes do update)
        categorias_antigas = await categorias_coll.find({}).to_list(length=None)
        api_logger.debug(f"Categorias antigas: {[c['id'] for c in categorias_antigas]}")

        # 2. Remove todas categorias antigas
        del_result = await categorias_coll.delete_many({})
        api_logger.debug(f"Removeu {del_result.deleted_count} categorias antigas.")

        # 3. Define mapa antigo para novo por id (caso precise validar nomes, etc)
        novo_mapa = {str(cat.get("id")): cat for cat in new_groups}

        # 4. Adiciona as novas categorias do payload
        if new_groups:
            for grupo in new_groups:
                categoria_id = str(grupo.get("id"))
                grupo_data = {
                    "id": categoria_id,
                    "categoria_nome": grupo.get("categoria_nome"),
                    "natureza": grupo.get("natureza"),
                    "limite": grupo.get("limite"),
                    "subcategorias": grupo.get("subcategorias", []),
                    "updated_at": now,
                }
                await categorias_coll.insert_one(grupo_data)
                api_logger.debug(f"Adicionada categoria nova id={categoria_id}")

        # 5. Atualiza as transações para refletir novos dados das categorias removidas
        for cat_antiga in categorias_antigas:
            cat_id = str(cat_antiga.get("id"))
            grupo_novo = novo_mapa.get(cat_id)
            if not grupo_novo:
                continue  # Categoria removida definitivamente
            # Atualize os campos desejados nas transações (exemplo, categoria_nome e natureza)
            upd_result = await transacoes_coll.update_many(
                {"categoria.id": cat_id},
                {"$set": {
                    "categoria.categoria_nome": grupo_novo.get("categoria_nome"),
                    "categoria.natureza": grupo_novo.get("natureza"),
                    "categoria.limite": grupo_novo.get("limite")
                }}
            )
            api_logger.debug(f"Atualizadas {upd_result.modified_count} transações para categoria id={cat_id}")

        return LimitsResponse.model_validate(new_groups)

    except Exception as e:
        tb_str = traceback.format_exc()
        api_logger.error(f"Error saving limits: {str(e)}\n{tb_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar limites",
        )
