# app/db/repositories/transacao.py

from typing import List, Optional
from datetime import datetime, time

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.db.models.transacao import TransacaoORM
from app.db.repositories.categoria import CategoriaRepository
from app.db.repositories.subcategoria import SubcategoriaRepository
from app.schemas.transacao import TipoPagamento, TipoTransacao, TransacaoCreate, TransacaoUpdate
from app.schemas.categorias import CategoriaCreate
from app.schemas.subcategoria import SubcategoriaCreate
from app.logger import log_database_operation

from uuid import uuid4
from dateutil.relativedelta import relativedelta


class TransacaoRepository:
    def __init__(self, db: AsyncSession = Depends(get_session)):
        self.db = db
        self.categoria_repo = CategoriaRepository(db)
        self.subcategoria_repo = SubcategoriaRepository(db)

    def _calcular_valor_parcela(self, valor_total: float, total_parcelas: int) -> float:
        return round(valor_total / total_parcelas, 2)
    
    def _gerar_datas_parcelas(self, data_base: datetime, total_parcelas: int) -> List[datetime]:
        dates = []

        for i in range(total_parcelas):
            if i == 0:
                dates.append(data_base)
            else:
                proximo_mês = data_base + relativedelta(months=i)
                dates.append(proximo_mês.replace(day=1))
        
        return dates
    
    def _create_transacaoes(
            self,
            obj_in,
            group_id: str,
            parcela: int,
            total_parcelas: int,
            valor: float,
            data_transacao: datetime,
            categoria_id=int,
            sub_id=int
    ) -> TransacaoORM:
        return TransacaoORM(
            group_id=group_id,
            tipo=obj_in.tipo,
            valor=valor,
            descricao=f'{obj_in.descricao} - parcela {parcela}/{total_parcelas}',
            data_transacao=data_transacao,
            forma_pagamento=obj_in.forma_pagamento,
            natureza=obj_in.natureza,
            parcela=parcela,  
            total_parcelas=total_parcelas,
            categoria_id=categoria_id,
            subcategoria_id=sub_id,

        )
    
    def _ajustar_ultima_parcela(self, transacoes: List, valor: float):
        if not transacoes:
            return
        
        total_parcelas = sum(t.valor for t in transacoes)
        diferenca = round(valor - total_parcelas, 2)

        if diferenca != 0:
            transacoes[0].valor = round(transacoes[0].valor + diferenca, 2)
    
    async def _create_transacaoes_parceladas(self, 
                                      obj_in, 
                                      group_id: str, 
                                      categoria_id: int,
                                      sub_id: int
                                      ):
        total_parcelas = obj_in.total_parcelas
        valor = self._calcular_valor_parcela(obj_in.valor, total_parcelas)
        datas_parcelas = self._gerar_datas_parcelas(obj_in.data_transacao, total_parcelas)

        created_transactions = []

        for i in range(total_parcelas):
            transacao = self._create_transacaoes(
                obj_in=obj_in,
                group_id=group_id,
                parcela=i + 1,
                total_parcelas=total_parcelas,
                valor=valor,
                data_transacao=datas_parcelas[i],
                categoria_id=categoria_id,
                sub_id=sub_id
            )
            self.db.add(transacao)
            created_transactions.append(transacao)

        self._ajustar_ultima_parcela(created_transactions, obj_in.valor)

        await self.db.commit()

        for transacao in created_transactions:
            await self.db.refresh(transacao)

        return created_transactions

    async def create(self, obj_in: TransacaoCreate) -> TransacaoORM:
        log = log_database_operation(operation="create", collection="transacoes", payload=obj_in.model_dump())
        group_id = uuid4()

        # 1) Categoria: se id não informado, busca ou cria por nome
        if obj_in.categoria_id is not None:
            categoria = await self.categoria_repo.get_by_id(obj_in.categoria_id)
            if not categoria:
                raise HTTPException(status_code=400, detail="Categoria não encontrada")
        else:
            categoria = await self.categoria_repo.get_by_nome(obj_in.categoria_nome)
            if not categoria:
                categoria = await self.categoria_repo.create(
                    CategoriaCreate(
                        categoria_nome=obj_in.categoria_nome,
                        natureza=obj_in.natureza,
                        limite=0,
                        subcategorias=[]
                    )
                )

        # 2) Subcategoria: se id não informado, busca ou cria por nome sob a categoria
        if obj_in.subcategoria_id is not None:
            sub = await self.subcategoria_repo.get_by_id(obj_in.subcategoria_id)
            if not sub or sub.categoria_id != categoria.id:
                raise HTTPException(status_code=400, detail="Subcategoria inválida")
        else:
            sub = await self.subcategoria_repo.get_by_nome_and_categoria(
                obj_in.subcategoria_nome, categoria.id
            )
            if not sub:
                sub = await self.subcategoria_repo.create(
                    categoria_id=categoria.id,
                    obj_in=SubcategoriaCreate(subcategoria_nome=obj_in.subcategoria_nome)
                )

        # 3) Cria a transação usando os IDs resolvidos
        try:
            if (obj_in.forma_pagamento == TipoPagamento.CREDITO and obj_in.total_parcelas > 1):
                transacoes = await self._create_transacaoes_parceladas(obj_in, group_id, categoria.id, sub.id)
                log.info(f"Transação {group_id} criada, com {len(transacoes)} parcelas")
                return transacoes[0]
            else: 
                inst = TransacaoORM(
                    valor=obj_in.valor,
                    descricao=obj_in.descricao,
                    parcela=obj_in.parcelas,
                    total_parcelas=obj_in.total_parcelas,
                    data_transacao=obj_in.data_transacao,
                    tipo=obj_in.tipo.value,
                    natureza=obj_in.natureza.value,
                    forma_pagamento=obj_in.forma_pagamento.value,
                    categoria_id=categoria.id,
                    subcategoria_id=sub.id,
                    group_id=group_id
                )


            self.db.add(inst)
            await self.db.commit()
            await self.db.refresh(inst)
            log.info(f"Transação {inst.id} criada")
            return inst
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail="Erro ao criar transação")

    async def get_all(
        self,
        data_inicio: Optional[datetime] = None,
        data_final: Optional[datetime] = None
    ) -> List[TransacaoORM]:
        stmt = select(TransacaoORM).options(
            selectinload(TransacaoORM.categoria),
            selectinload(TransacaoORM.subcategoria)
        )
        if data_inicio:
            stmt = stmt.where(TransacaoORM.data_transacao >= data_inicio)
        if data_final:
        # Ajusta para incluir toda a faixa do dia final
            data_final_completo = datetime.combine(data_final.date(), time.max)
            stmt = stmt.where(TransacaoORM.data_transacao <= data_final_completo)

        stmt = stmt.order_by(TransacaoORM.data_transacao.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, id: int) -> Optional[TransacaoORM]:
        stmt = select(TransacaoORM).options(
            selectinload(TransacaoORM.categoria),
            selectinload(TransacaoORM.subcategoria)
        ).where(TransacaoORM.id == id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update(self, id: int, obj_in: TransacaoUpdate) -> Optional[TransacaoORM]:
        trans = await self.get_by_id(id)
        if not trans:
            return None

        # 1) Se categoria_id ou categoria_nome vierem, resolve/cria
        if obj_in.categoria_id is not None or obj_in.categoria_nome is not None:
            if obj_in.categoria_id is not None:
                categoria = await self.categoria_repo.get_by_id(obj_in.categoria_id)
                if not categoria:
                    raise HTTPException(status_code=400, detail="Categoria não encontrada")
            else:
                categoria = await self.categoria_repo.get_by_nome(obj_in.categoria_nome)
                if not categoria:
                    categoria = await self.categoria_repo.create(
                        CategoriaCreate(
                            categoria_nome=obj_in.categoria_nome,
                            natureza=obj_in.natureza or trans.natureza_transacao,
                            limite=0,
                            subcategorias=[]
                        )
                    )
            trans.categoria_id = categoria.id

        # 2) Se subcategoria_id ou subcategoria_nome vierem, resolve/cria
        if obj_in.subcategoria_id is not None or obj_in.subcategoria_nome is not None:
            if obj_in.subcategoria_id is not None:
                sub = await self.subcategoria_repo.get_by_id(obj_in.subcategoria_id)
                if not sub or sub.categoria_id != trans.categoria_id:
                    raise HTTPException(status_code=400, detail="Subcategoria inválida")
            else:
                sub = await self.subcategoria_repo.get_by_nome_and_categoria(
                    obj_in.subcategoria_nome, trans.categoria_id
                )
                if not sub:
                    sub = await self.subcategoria_repo.create(
                        categoria_id=trans.categoria_id,
                        obj_in=SubcategoriaCreate(subcategoria_nome=obj_in.subcategoria_nome)
                    )
            trans.subcategoria_id = sub.id

        # 3) Atualiza demais campos
        data = obj_in.model_dump(exclude_unset=True, exclude={
            "categoria_id", "categoria_nome", "subcategoria_id", "subcategoria_nome"
        })
        for field, val in data.items():
            setattr(trans, field, val)

        try:
            await self.db.commit()
            await self.db.refresh(trans)
            return trans
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail="Erro ao atualizar transação")

    async def delete(self, id: int) -> Optional[TransacaoORM]:
        trans = await self.get_by_id(id)
        if not trans:
            return None
        await self.db.delete(trans)
        await self.db.commit()
        return trans
