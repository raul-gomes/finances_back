# app/db/repositories/categoria.py

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update
from sqlalchemy.exc import IntegrityError

from app.core.database import get_session
from app.db.models.categoria import CategoriaORM
from app.db.repositories.subcategoria import SubcategoriaRepository
from app.schemas.categorias import CategoriaCreate, CategoriaUpdate
from app.logger import log_database_operation

class CategoriaRepository:
    """
    Repositório para operações CRUD de Categoria e sincronização de Subcategoria.
    """

    def __init__(self, db: AsyncSession = Depends(get_session)):
        self.db = db
        self.model = CategoriaORM
        self.sub_repo = SubcategoriaRepository(db)

    async def get_by_id(self, id: int) -> Optional[CategoriaORM]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_by_nome(self, nome: str) -> Optional[CategoriaORM]:
        result = await self.db.execute(select(self.model).where(self.model.categoria_nome == nome))
        return result.scalars().first()
    
    async def create(self, obj_in: CategoriaCreate) -> CategoriaORM:
        """
        Insere uma nova categoria e suas subcategorias (se houver).
        Lança HTTPException em caso de erro de unicidade.
        """
        log = log_database_operation(operation="create", collection="categorias", payload=obj_in.model_dump())
        try:
            instance = self.model(**obj_in.model_dump(exclude={"subcategorias"}))
            self.db.add(instance)
            await self.db.commit()
            await self.db.refresh(instance)

            if obj_in.subcategorias:
                await self.sub_repo.create_many(instance.id, obj_in.subcategorias)

            # Recarrega categoria completa
            result = await self.db.execute(select(self.model).where(self.model.id == instance.id))
            categoria = result.scalars().first()
            log.info(f"Categoria {categoria.id} criada")
            return categoria

        except IntegrityError as e:
            await self.db.rollback()
            if "categorias.categoria_nome" in str(e):
                log.error("Violação de unicidade em categoria_nome")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Categoria com nome '{obj_in.categoria_nome}' já existe"
                )
            log.error(f"Erro de integridade no banco: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro de integridade no banco de dados"
            )

    async def get_all(self) -> List[CategoriaORM]:
        """
        Recupera todas as categorias, incluindo subcategorias.
        """
        log = log_database_operation(operation="read_all", collection="categorias")
        stmt = select(self.model).order_by(self.model.categoria_nome)
        result = await self.db.execute(stmt)
        categorias = result.unique().scalars().all()
        log.info(f"{len(categorias)} categorias recuperadas")
        return categorias

    async def get_by_id(self, id: int) -> Optional[CategoriaORM]:
        """
        Busca uma categoria pelo ID.
        """
        log = log_database_operation(operation="read", collection="categorias", categoria_id=id)
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        categoria = result.scalars().first()
        if categoria:
            log.info(f"Categoria {id} encontrada")
        else:
            log.warning(f"Categoria {id} não encontrada")
        return categoria

    async def update(self, id: int, obj_in: CategoriaUpdate) -> Optional[CategoriaORM]:
        categoria = await self.get_by_id(id)
        if not categoria:
            return None

        # 1) Unicidade de nome
        if obj_in.categoria_nome:
            conflict = (await self.db.execute(
                select(self.model)
                .where(self.model.categoria_nome == obj_in.categoria_nome, self.model.id != id)
            )).scalars().first()
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Outra categoria com nome '{obj_in.categoria_nome}' já existe"
                )

        # 2) Atualiza campos básicos
        base = obj_in.model_dump(exclude_unset=True, exclude={"subcategorias"})
        for field, val in base.items():
            setattr(categoria, field, val)
        await self.db.commit()

        # 3) Sincroniza subcategorias sem deletar as existentes
        incoming = obj_in.subcategorias or []

        # Mapear IDs existentes para atualização
        for sub in incoming:
            if sub.id is not None:
                await self.sub_repo.update(sub.id, sub)

        # Criar apenas as novas (sem id)
        new_subs = [s for s in incoming if s.id is None]
        if new_subs:
            await self.sub_repo.create_many(categoria.id, new_subs)

        # 4) Recarrega e retorna
        await self.db.refresh(categoria)
        return categoria

    async def delete(self, id: int) -> Optional[CategoriaORM]:
        """
        Remove uma categoria pelo ID.
        """
        log = log_database_operation(operation="delete", collection="categorias", categoria_id=id)
        categoria = await self.get_by_id(id)
        if not categoria:
            return None
        await self.db.delete(categoria)
        await self.db.commit()
        log.info(f"Categoria {id} excluída")
        return categoria
