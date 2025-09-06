from datetime import datetime
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.db.models.transacao import TransacaoORM
from app.schemas.transacao import TransacaoCreate
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

class TransacaoRepository:
    def __init__(self, db: AsyncSession = Depends(get_session)):
        self.model = TransacaoORM
        self.db = db

    async def create(self, obj_in: TransacaoCreate):
        obj = self.model(**obj_in.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    
    async def get_all(
            self,
            data_inicio: Optional[datetime] = None,
            data_final: Optional[datetime] = None
    ):
        query = select(self.model).options(
            selectinload(self.model.categoria),
            selectinload(self.model.subcategoria)
        )

        if data_inicio:
            query = query.where(self.model.data_transacao >= data_inicio)
        
        if data_final:
            query = query.where(self.model.data_transacao <= data_final)
        
        query = query.order_by(self.model.data_transacao.desc())

        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_id(self, id:int):
        result = await self.db.execute(
            select(self.model)
            .options(
                selectinload(self.model.categoria),
                selectinload(self.model.subcategoria)
            )
            .where(self.model.id == id)
        )
        return result.scalars().first()
    
    