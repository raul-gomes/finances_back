# app/db/repositories/subcategoria.py

from typing import List, Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, delete
from sqlalchemy.exc import IntegrityError

from app.core.database import get_session
from app.db.models.categoria import SubcategoriaORM
from app.logger import log_database_operation
from app.schemas.categorias import Subcategoria, SubcategoriaUpdate
from app.schemas.subcategoria import SubcategoriaCreate


class SubcategoriaRepository:
    def __init__(self, db: AsyncSession = Depends(get_session)):
        self.db = db
        self.model = SubcategoriaORM

    async def get_by_id(self, id: int) -> Optional[SubcategoriaORM]:
        return await self.db.get(self.model, id)

    async def get_by_nome_and_categoria(self, nome: str, categoria_id: int) -> Optional[SubcategoriaORM]:
        result = await self.db.execute(
            select(self.model).where(
                self.model.subcategoria_nome == nome,
                self.model.categoria_id == categoria_id
            )
        )
        return result.scalars().first()
    
    async def create(self, categoria_id: int, obj_in: SubcategoriaCreate) -> SubcategoriaORM:
        log = log_database_operation(operation="create", collection="subcategorias", payload=obj_in.dict())
        try:
            inst = self.model(subcategoria_nome=obj_in.subcategoria_nome, categoria_id=categoria_id)
            self.db.add(inst)
            await self.db.commit()
            await self.db.refresh(inst)
            log.info(f"Subcategoria {inst.id} criada para categoria {categoria_id}")
            return inst
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail="Erro ao criar subcategoria")

    async def create_many(self, categoria_id: int, subs: List[SubcategoriaCreate]):
        stmt = insert(self.model).values([
            {'subcategoria_nome': s.subcategoria_nome, 'categoria_id': categoria_id}
            for s in subs
        ])
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_by_categoria(self, categoria_id: int) -> List[SubcategoriaORM]:
        """Busca todas as subcategorias de uma categoria"""
        result = await self.db.execute(
            select(self.model).where(self.model.categoria_id == categoria_id)
        )
        return result.scalars().all()

    async def update(self, id: int, obj_in: SubcategoriaUpdate) -> Optional[SubcategoriaORM]:
        """Atualiza uma subcategoria"""
        sub = await self.db.get(self.model, id)
        if not sub:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"id"})
        for field, value in update_data.items():
            setattr(sub, field, value)
        
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def delete(self, id: int) -> Optional[SubcategoriaORM]:
        """Deleta uma subcategoria"""
        sub = await self.db.get(self.model, id)
        if not sub:
            return None
        
        await self.db.delete(sub)
        await self.db.commit()
        return sub

    async def delete_by_categoria(self, categoria_id: int) -> None:
        """Deleta todas as subcategorias de uma categoria"""
        await self.db.execute(
            delete(self.model).where(self.model.categoria_id == categoria_id)
        )
        await self.db.commit()
