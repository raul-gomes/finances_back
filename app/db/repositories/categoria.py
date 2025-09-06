from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.db.models.categoria import CategoriaORM, SubcategoriaORM
from app.schemas.categorias import CategoriaCreate, CategoriaUpdate, SubcategoriaUpdate
from typing import List, Optional

class CategoriaRepository:
    def __init__(self, db: AsyncSession = Depends(get_session)):
        self.db = db
        self.model = CategoriaORM
        self.sub_repo = SubcategoriaORM

    async def create(self, obj_in: CategoriaCreate) -> CategoriaORM:
        categoria = self.model(**obj_in.model_dump(exclude={'subcategorias'}))
        self.db.add(categoria)
        await self.db.commit()
        await self.db.refresh(categoria)

        if obj_in.subcategorias:
            await self.sub_repo.create_many(categoria.id, obj_in.subcategorias)
            await self.db.refresh(categoria)

        return categoria
    
    async def get_all(self) -> List[CategoriaORM]:
        query = (
            select(self.model)
            .options(selectinload(self.model.subcategorias))
            .order_by(self.model.categoria_nome)
        )
        result = await self.db.execute(query)

        return result.scalars().all()
    
    async def get_by_id(self, id:int) -> Optional[CategoriaORM]:
        query = (
            select(self.model)
            .options(selectinload(self.sub_repo))
            .where(self.model.id == id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def update(self, id: int, obj_in: CategoriaUpdate) -> Optional[CategoriaORM]:
        categoria = await self.get_by_id(id)
        if not categoria:
            return None

        # 1) Atualiza campos básicos da categoria
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"subcategorias"})
        for field, value in update_data.items():
            setattr(categoria, field, value)
        await self.db.commit()

        # 2) Sincroniza subcategorias
        existing_subs = categoria.subcategorias  # lista de SubcategoriaORM
        existing_map = {sub.id: sub for sub in existing_subs}

        # IDs recebidos no payload
        incoming: List[SubcategoriaUpdate] = obj_in.subcategorias or []
        incoming_ids = {s.id for s in incoming if s.id is not None}

        # 2a) Deletar subcategorias que não estão no incoming_ids
        for sub in existing_subs:
            if sub.id not in incoming_ids:
                await self.sub_repo.delete(sub.id)

        # 2b) Atualizar subcategorias existentes
        for s in incoming:
            if s.id is not None and s.id in existing_map:
                await self.sub_repo.update(s.id, s)

        # 2c) Criar novas subcategorias (sem id)
        new_subs = [s for s in incoming if s.id is None]
        if new_subs:
            await self.sub_repo.create_many(categoria.id, new_subs)

        # 3) Recarrega relação completa
        await self.db.refresh(categoria)
        return categoria
    
    async def delete(self, id: int) -> Optional[CategoriaORM]:
        categoria = await self.get_by_id(id)
        if not categoria:
            return None
        
        await self.db.delete(categoria)
        await self.db.commit()
        return categoria


