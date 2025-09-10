# app/db/repositories/limits.py

from typing import List, Dict, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_session
from app.db.models.categoria import CategoriaORM, SubcategoriaORM

from app.db.repositories.categoria import CategoriaRepository
from app.db.repositories.subcategoria import SubcategoriaRepository
from app.schemas.limits import LimitsUpdatePayload, LimitsUpdateResponse, CategoriaLimiteUpdate
from app.schemas.categorias import CategoriaCreate, CategoriaUpdate
from app.schemas.subcategoria import SubcategoriaCreate, SubcategoriaUpdate
from app.logger import log_database_operation


class LimitsRepository:
    """
    Repositório especializado para operações em lote de limites de categorias/subcategorias.
    """

    def __init__(self, db: AsyncSession = Depends(get_session)):
        self.db = db
        self.categoria_repo = CategoriaRepository(db)
        self.subcategoria_repo = SubcategoriaRepository(db)

    async def bulk_update_limits(self, payload: LimitsUpdatePayload) -> LimitsUpdateResponse:
        """
        Processa atualizações em lote de limites de categorias e subcategorias.
        """
        log = log_database_operation(
            operation="bulk_update_limits",
            collection="categorias",
            payload=payload.model_dump()
        )

        response = LimitsUpdateResponse(
            success=True,
            message="Limites atualizados com sucesso"
        )

        try:
            # Processa categorias novas
            for new_cat in payload.new:
                try:
                    await self._create_new_category(new_cat, response)
                except Exception as e:
                    response.errors.append(f"Erro ao criar categoria '{new_cat.categoria_nome}': {str(e)}")
                    log.error(f"Erro ao criar categoria: {e}")

            # Processa categorias modificadas
            for mod_cat in payload.modified:
                try:
                    await self._update_existing_category(mod_cat, response)
                except Exception as e:
                    response.errors.append(f"Erro ao atualizar categoria ID {mod_cat.id}: {str(e)}")
                    log.error(f"Erro ao atualizar categoria: {e}")

            # Commit final se não houver erros críticos
            await self.db.commit()

            if response.errors:
                response.success = False
                response.message = f"Operação concluída com {len(response.errors)} erro(s)"

            log.info(f"Bulk update concluído: {response.created_categories} criadas, {response.updated_categories} atualizadas")
            return response

        except Exception as e:
            await self.db.rollback()
            log.error(f"Erro crítico no bulk update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao processar limites: {str(e)}"
            )

    async def _create_new_category(self, new_cat: CategoriaLimiteUpdate, response: LimitsUpdateResponse):
        """Cria uma nova categoria com suas subcategorias."""
        
        # Verifica se já existe categoria com mesmo nome
        existing = await self.categoria_repo.get_by_nome(new_cat.categoria_nome)
        if existing:
            raise ValueError(f"Categoria '{new_cat.categoria_nome}' já existe")

        # Cria a categoria
        categoria_create = CategoriaCreate(
            categoria_nome=new_cat.categoria_nome,
            natureza=new_cat.natureza,
            limite=new_cat.limite,
            subcategorias=[]  # Vamos criar as subcategorias separadamente
        )

        categoria = await self.categoria_repo.create(categoria_create)
        response.created_categories += 1

        # Cria subcategorias associadas
        for sub_data in new_cat.subcategorias:
            if sub_data.subcategoria_nome.strip():  # Só cria se tiver nome
                sub_create = SubcategoriaCreate(
                    subcategoria_nome=sub_data.subcategoria_nome
                )
                await self.subcategoria_repo.create(categoria.id, sub_create)
                response.created_subcategories += 1

    async def _update_existing_category(self, mod_cat: CategoriaLimiteUpdate, response: LimitsUpdateResponse):
        """Atualiza uma categoria existente e suas subcategorias."""
        
        if not mod_cat.id:
            raise ValueError("ID da categoria é obrigatório para atualização")

        # Verifica se a categoria existe
        categoria = await self.categoria_repo.get_by_id(mod_cat.id)
        if not categoria:
            raise ValueError(f"Categoria ID {mod_cat.id} não encontrada")

        # Atualiza campos básicos da categoria
        categoria_update = CategoriaUpdate(
            categoria_nome=mod_cat.categoria_nome,
            natureza=mod_cat.natureza,
            limite=mod_cat.limite,
            subcategorias=[]  # Processaremos separadamente
        )

        await self.categoria_repo.update(mod_cat.id, categoria_update)
        response.updated_categories += 1

        # Processa subcategorias
        await self._process_subcategories(mod_cat.id, mod_cat.subcategorias, response)

    async def _process_subcategories(self, categoria_id: int, subcategorias: List, response: LimitsUpdateResponse):
        """Processa subcategorias de uma categoria (novas e atualizações)."""
        
        for sub_data in subcategorias:
            if not sub_data.subcategoria_nome.strip():  # Ignora vazias
                continue

            if sub_data.id:
                # Subcategoria existente - atualizar
                sub_update = SubcategoriaUpdate(
                    subcategoria_nome=sub_data.subcategoria_nome
                )
                updated_sub = await self.subcategoria_repo.update(sub_data.id, sub_update)
                if updated_sub:
                    response.updated_subcategories += 1
            else:
                # Nova subcategoria - criar
                sub_create = SubcategoriaCreate(
                    subcategoria_nome=sub_data.subcategoria_nome
                )
                await self.subcategoria_repo.create(categoria_id, sub_create)
                response.created_subcategories += 1

    async def get_all_limits(self) -> List[Dict[str, Any]]:
        """
        Retorna todas as categorias formatadas para o frontend de limites.
        """
        log = log_database_operation(operation="get_all_limits", collection="categorias")
        
        # Busca todas as categorias com subcategorias
        stmt = select(CategoriaORM).order_by(CategoriaORM.categoria_nome)
        result = await self.db.execute(stmt)
        categorias = result.scalars().all()

        # Formata para o frontend
        formatted_data = []
        for cat in categorias:
            # Busca subcategorias da categoria
            sub_stmt = select(SubcategoriaORM).where(SubcategoriaORM.categoria_id == cat.id)
            sub_result = await self.db.execute(sub_stmt)
            subcategorias = sub_result.scalars().all()

            categoria_data = {
                "id": cat.id,
                "categoria_nome": cat.categoria_nome,
                "natureza": cat.natureza,
                "limite": cat.limite,
                "subcategorias": [
                    {
                        "id": sub.id,
                        "subcategoria_nome": sub.subcategoria_nome
                    }
                    for sub in subcategorias
                ]
            }
            formatted_data.append(categoria_data)

        log.info(f"{len(formatted_data)} categorias recuperadas para limites")
        return formatted_data