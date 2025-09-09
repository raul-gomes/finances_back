from pydantic import BaseModel, Field
from typing import Any, Dict, List
from datetime import datetime
from app.schemas.transacao import TransacaoResponse


class ExtratoResponse(BaseModel):
    entradas: float = Field(..., description="Total de entradas no período")
    saidas: float = Field(..., description="Total de saídas no período")
    data_inicial: str = Field(..., description="Data inicial do filtro (dd/mm/yyyy)")
    data_final: str = Field(..., description="Data final do filtro (dd/mm/yyyy)")
    meta_mensal: float = Field(..., description="Meta mensal financeira")
    total_investido: float = Field(..., description="Total investido (igual às entradas)")
    transacoes: List[TransacaoResponse] = Field(..., description="Lista de transações filtradas")  # SEM Ç

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

class SubcategoriaGasto(BaseModel):
    nome: str = Field(..., description="Nome da subcategoria")
    valor: str = Field(..., description="Valor gasto na subcategoria formatado")


class CategoriaGasto(BaseModel):
    nome: str = Field(..., description="Nome da categoria")
    total: float = Field(..., description="Total gasto na categoria")
    limite: float = Field(..., description="Limite financeiro da categoria")
    subcategorias: List[SubcategoriaGasto] = Field(..., description="Lista de gastos por subcategoria")


class GastosPorCategoriaResponse(BaseModel):
    data_inicial: str = Field(..., description="Data inicial do filtro (DD/MM/YYYY)")
    data_final: str = Field(..., description="Data final do filtro (DD/MM/YYYY)")
    categorias: List[CategoriaGasto] = Field(..., description="Categorias com gastos detalhados")

    class Config:
        from_attributes = True


class SubcategoriaOpcao(BaseModel):
    nome: str = Field(..., description="Nome da subcategoria")

class CategoriaOpcao(BaseModel):
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