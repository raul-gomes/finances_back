from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.core.database import get_session
from app.db.models.categoria import CategoriaORM
from app.db.repositories.subcategoria import SubcategoriaRepository
from app.schemas.categorias import CategoriaCreate, CategoriaUpdate, SubcategoriaUpdate
from typing import List, Optional

class CategoriaRepository:
    def __init__(self, db: AsyncSession = Depends(get_session)):
        self.db = db
        self.model = CategoriaORM
        self.sub_repo = SubcategoriaRepository(db)

    async def create(self, obj_in: CategoriaCreate) -> CategoriaORM:
        try:
            categoria = self.model(**obj_in.model_dump(exclude={'subcategorias'}))
            self.db.add(categoria)
            await self.db.commit()
            await self.db.refresh(categoria)

            if obj_in.subcategorias:
                await self.sub_repo.create_many(categoria.id, obj_in.subcategorias)                

            result = await self.db.execute(
                select(self.model)
                .where(self.model.id == categoria.id)
            )
        
            return result.scalars().first()
        
        except IntegrityError as e:
            await self.db.rollback()
            if 'categorias.categoria_nome' in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Categoria com nome '{obj_in.categoria_nome}' já existe"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro de integridade no banco de dados"
            )
    
    async def get_all(self) -> List[CategoriaORM]:
        
        stmt = select(self.model).options(
            # joined eager loading ou selectinload
            selectinload(self.model.subcategorias)
        ).order_by(self.model.categoria_nome)

        result = await self.db.execute(stmt)
        # deduplica instâncias de CategoriaORM
        categorias = result.unique().scalars().all()
        return categorias
    
    async def get_by_id(self, id:int) -> Optional[CategoriaORM]:
        query = (
            select(self.model)
            .where(self.model.id == id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def update(self, id: int, obj_in: CategoriaUpdate) -> Optional[CategoriaORM]:
        categoria = await self.get_by_id(id)
        if not categoria:
            return None

        # 1) Unicidade de nome
        if obj_in.categoria_nome:
            q = select(self.model).where(
                self.model.categoria_nome == obj_in.categoria_nome,
                self.model.id != id
            )
            other = (await self.db.execute(q)).scalars().first()
            if other:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Outra categoria com nome '{obj_in.categoria_nome}' já existe"
                )

            # 2) Atualiza campos básicos
            base_data = obj_in.model_dump(exclude_unset=True, exclude={"subcategorias"})
            for field, value in base_data.items():
                setattr(categoria, field, value)
            await self.db.commit()
        
            # 3) Sincroniza subcategorias
            existing = {sub.id: sub for sub in categoria.subcategorias}
            incoming = obj_in.subcategorias or []
            incoming_ids = {s.id for s in incoming if s.id is not None}
        
            # 3a) Deleta ausentes
            for sub_id in set(existing) - incoming_ids:
                await self.sub_repo.delete(sub_id)
        
            # 3b) Atualiza existentes
            for s in incoming:
                if s.id is not None:
                    await self.sub_repo.update(s.id, s)
        
            # 3c) Cria novos
            new = [s for s in incoming if s.id is None]
            if new:
                await self.sub_repo.create_many(categoria.id, new)
        
            # 4) Recarrega tudo
            await self.db.refresh(categoria)
            return categoria

    
    async def delete(self, id: int) -> Optional[CategoriaORM]:
        categoria = await self.get_by_id(id)
        if not categoria:
            return None
        
        await self.db.delete(categoria)
        await self.db.commit()
        return categoria


