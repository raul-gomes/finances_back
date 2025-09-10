from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

from enum import Enum

from app.schemas.transacao import NaturezaTransacao, TipoPagamento, TipoTransacao

class TransacaoExtrato(BaseModel):
    id: int = Field(..., description="ID da transação")
    valor: float = Field(..., description="Valor da transação")
    descricao: str = Field(..., description="Descrição da transação")
    parcelas: Optional[int] = Field(None, description="Parcelas, se houver")
    total_parcelas: Optional[int] = Field(None, description="Total de parcelas")
    data_transacao: datetime = Field(..., description="Data e hora da transação")
    tipo: TipoTransacao = Field(..., description="Tipo: entrada ou saida")
    natureza_transacao: NaturezaTransacao = Field(..., description="Natureza: pf ou pj")
    forma_pagamento: TipoPagamento = Field(..., description="Forma de pagamento")
    categoria: str = Field(..., description="Nome da categoria")
    subcategoria: str = Field(..., description="Nome da subcategoria")
    data_criacao: datetime = Field(..., description="Timestamp de criação")
    data_atualizacao: datetime = Field(..., description="Timestamp de atualização")

    class Config:
        from_attributes = True


class ExtratoResponse(BaseModel):
    entradas: float = Field(..., description="Total de entradas no período")
    saidas: float = Field(..., description="Total de saídas no período")
    data_inicial: str = Field(..., description="Data inicial do filtro (dd/mm/yyyy)")
    data_final: str = Field(..., description="Data final do filtro (dd/mm/yyyy)")
    meta_mensal: float = Field(..., description="Meta mensal financeira")
    total_investido: float = Field(..., description="Total investido (igual às entradas)")
    transacoes: List[TransacaoExtrato] = Field(..., description="Lista de transações filtradas")

    class Config:
        from_attributes = True


class MesRendimento(BaseModel):
    entrada: float = Field(..., description="Total de entradas no mês")
    saida: float = Field(..., description="Total de saídas no mês")


class RendimentoPeriodoResponse(BaseModel):
    limite: float = Field(..., description="Limite/metas financeiras")
    meses: Dict[str, MesRendimento] = Field(..., description="Dados de entrada e saída por mês em minúsculo")

    class Config:
        from_attributes = True

# app/schemas/dashboard.py

class TipoTrans(Enum):
    entrada = "entrada"
    saida = "saida"

class SubcategoriaGasto(BaseModel):
    nome: str = Field(..., description="Nome da subcategoria")
    valor: str = Field(..., description="Valor agregado à subcategoria")


class CategoriaGasto(BaseModel):
    nome: str = Field(..., description="Nome da categoria")
    total: float = Field(..., description="Total agregado na categoria")
    limite: float = Field(..., description="Limite configurado na categoria")
    subcategorias: List[SubcategoriaGasto] = Field(
        ..., description="Detalhamento por subcategoria"
    )


class GastosPorCategoriaResponse(BaseModel):
    data_inicial: str = Field(..., description="Data inicial do filtro (DD/MM/YYYY)")
    data_final: str = Field(..., description="Data final do filtro (DD/MM/YYYY)")
    categorias: List[CategoriaGasto] = Field(
        ..., description="Categorias com valores agregados"
    )

    class Config:
        from_attributes = True

class SubcategoriaOpcao(BaseModel):
    id: int = Field(..., description="ID da subcategoria")
    nome: str = Field(..., description="Nome da subcategoria")

class CategoriaOpcao(BaseModel):
    id: int = Field(..., description="ID da categoria")
    categoria: str = Field(..., description="Nome da categoria")
    subcategorias: List[SubcategoriaOpcao] = Field(..., description="Lista de subcategorias")

class OpcoesCategoriaResponse(BaseModel):
    opcoes: List[CategoriaOpcao] = Field(..., description="Lista de categorias com suas subcategorias")
    class Config:
        from_attributes = True

class EntradasPorCategoriaResponse(BaseModel):
    data_inicial: str = Field(..., description="Data inicial do filtro (DD/MM/YYYY)")
    data_final: str = Field(..., description="Data final do filtro (DD/MM/YYYY)")
    subcategorias: List[Dict[str, Any]] = Field(..., description="Lista de categorias com entradas por subcategoria")
    
    class Config:
        from_attributes = True