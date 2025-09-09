# app/db/repositories/dashboard.py

import calendar
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.models.transacao import TransacaoORM
from app.db.models.categoria import CategoriaORM
from app.schemas.dashboard import CategoriaOpcao, EntradasPorCategoriaResponse, ExtratoResponse, OpcoesCategoriaResponse, RendimentoPeriodoResponse, SubcategoriaOpcao
from app.schemas.transacao import TransacaoResponse

class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def gastos_por_categoria(
        self,
        data_inicio: datetime,
        data_final: datetime,
        natureza: str,
    ) -> List[Dict[str, Any]]:

        # Busca todas transações do período, filtrando por natureza e saida, carregando categoria/subcategoria
        stmt = (
            select(TransacaoORM)
            .where(TransacaoORM.data_transacao >= data_inicio)
            .where(TransacaoORM.data_transacao <= data_final)
            .where(TransacaoORM.natureza == natureza)
            .where(TransacaoORM.tipo == "saida")
            .options(
                selectinload(TransacaoORM.categoria),
                selectinload(TransacaoORM.subcategoria)
            )
        )

        result = await self.db.execute(stmt)
        transacoes = result.unique().scalars().all()

        # Agregação dos dados
        gastos: Dict[int, Dict[str, Any]] = {}
        for t in transacoes:
            # Protege contra transações órfãs (sem categoria ou subcategoria)
            if not t.categoria or not t.subcategoria:
                continue
            cat_id = t.categoria.id
            cat_nome = t.categoria.categoria_nome
            sub_nome = t.subcategoria.subcategoria_nome
            limite = t.categoria.limite

            categoria_item = gastos.setdefault(cat_id, {
                "nome": cat_nome,
                "total": 0.0,
                "limite": limite,
                "subcategorias": {}
            })
            categoria_item["total"] += t.valor
            categoria_item["subcategorias"].setdefault(sub_nome, 0.0)
            categoria_item["subcategorias"][sub_nome] += t.valor

        # Monta lista final filtrando apenas categorias com total > 0
        resultado = []
        for cat_id, data in gastos.items():
            if data["total"] > 0:
                resultado.append({
                    "nome": data["nome"],
                    "total": round(data["total"], 2),
                    "limite": data["limite"],
                    "subcategorias": [
                        {"nome": sn, "valor": f"{round(v,2):.2f}"}
                        for sn, v in data["subcategorias"].items() if v > 0
                    ]
                })
        return resultado

    async def rendimento_por_periodo(
        self, 
        ano: int,
        natureza: str) -> Dict[str, Dict[str, float]]:

        meses_data: Dict[str, Dict[str, float]] = {}

        for m in range(1, 13):
            first = datetime(ano, m, 1)
            last_day = calendar.monthrange(ano, m)[1]
            last = datetime(ano, m, last_day, 23, 59, 59)

            stmt = (
                select(TransacaoORM)
                .where(TransacaoORM.data_transacao >= first)
                .where(TransacaoORM.data_transacao <= last)
                .where(TransacaoORM.natureza == natureza)
            )

            result = await self.db.execute(stmt)
            transacoes = result.unique().scalars().all()

            entradas = sum(t.valor for t in transacoes if t.tipo == "entrada")
            saidas = sum(t.valor for t in transacoes if t.tipo == "saida")

            meses_data[calendar.month_name[m].lower()] = {
                "entrada": round(entradas, 2),
                "saida": round(saidas, 2),
            }

        limite = 4000

        return RendimentoPeriodoResponse(limite=limite, meses=meses_data)
    
    async def extrato_financeiro(
        self, 
        data_inicio: datetime, 
        data_final: datetime, 
        natureza: str,
        data_inicio_str: str,
        data_final_str: str
    ) -> ExtratoResponse:
        
        # Buscar transações do período com relacionamentos
        stmt = (
            select(TransacaoORM)
            .where(TransacaoORM.data_transacao >= data_inicio)
            .where(TransacaoORM.data_transacao <= data_final)
            .where(TransacaoORM.natureza == natureza)
            .options(
                selectinload(TransacaoORM.categoria),
                selectinload(TransacaoORM.subcategoria)
            )
            .order_by(TransacaoORM.data_transacao.desc())
        )
        
        result = await self.db.execute(stmt)
        transacoes = result.unique().scalars().all()

        # Calcular totais
        entradas = sum(t.valor for t in transacoes if t.tipo == "entrada")
        saidas = sum(t.valor for t in transacoes if t.tipo == "saida")

        # Converter para schema de resposta
        txs = [TransacaoResponse.model_validate(t) for t in transacoes]

        meta_mensal = 4000.0  # valor fixo ou pode vir de configuração

        return ExtratoResponse(
            entradas=entradas,
            saidas=saidas,
            data_inicial=data_inicio_str,
            data_final=data_final_str,
            meta_mensal=meta_mensal,
            total_investido=entradas,  # conforme comentário no schema
            transacoes=txs
        )

    async def opcoes_categorias(self, natureza: str = 'all') -> OpcoesCategoriaResponse:
        
        stmt = select(CategoriaORM).options(
            selectinload(CategoriaORM.subcategorias)
        )
        
        if natureza != 'all':
            stmt = stmt.where(CategoriaORM.natureza == natureza)
        
        result = await self.db.execute(stmt)
        categorias = result.unique().scalars().all()
        
        opcoes: List[CategoriaOpcao] = []
        for categoria in categorias:
            subcategorias_lista = [
                SubcategoriaOpcao(nome=sub.subcategoria_nome) 
                for sub in categoria.subcategorias
            ]
            
            categoria_opcao = CategoriaOpcao(
                categoria=categoria.categoria_nome,
                subcategorias=subcategorias_lista
            )
            opcoes.append(categoria_opcao)
        
        return OpcoesCategoriaResponse(opcoes=opcoes)

    async def entradas_por_categoria(
        self, 
        data_inicio: datetime, 
        data_final: datetime, 
        natureza: str,
        data_inicio_str: str,
        data_final_str: str
    ) -> EntradasPorCategoriaResponse:
        
        # Buscar todas as categorias
        stmt_categorias = select(CategoriaORM)
        result = await self.db.execute(stmt_categorias)
        categorias = result.unique().scalars().all()
        
        output: List[Dict[str, Any]] = []
        
        for categoria in categorias:
            # Buscar transações de entrada para esta categoria
            stmt_transacoes = (
                select(TransacaoORM)
                .where(TransacaoORM.data_transacao >= data_inicio)
                .where(TransacaoORM.data_transacao <= data_final)
                .where(TransacaoORM.natureza == natureza)
                .where(TransacaoORM.categoria_id == categoria.id)
                .where(TransacaoORM.tipo == "entrada")
                .options(selectinload(TransacaoORM.subcategoria))
            )
            
            result_trans = await self.db.execute(stmt_transacoes)
            transacoes = result_trans.unique().scalars().all()
            
            subs: Dict[str, float] = {}
            total = 0.0
            
            for transacao in transacoes:
                valor = transacao.valor
                total += valor
                
                if transacao.subcategoria:
                    sub_nome = transacao.subcategoria.subcategoria_nome
                    subs.setdefault(sub_nome, 0.0)
                    subs[sub_nome] += valor
            
            # Só adiciona se tiver algum valor
            if total > 0:
                categoria_data = {
                    'total': round(total, 2),
                    categoria.categoria_nome.lower(): {k: round(v, 2) for k, v in subs.items()}
                }
                output.append(categoria_data)
        
        return EntradasPorCategoriaResponse(
            data_inicial=data_inicio_str,
            data_final=data_final_str,
            subcategorias=output
        )

