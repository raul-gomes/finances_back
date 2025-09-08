from pydantic import BaseModel, Field, ValidationInfo, model_validator, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class TipoTransacao(str, Enum):
    ENTRADA = 'entrada'
    SAIDA = 'saida'
    INVESTIMENTO = 'investimento'


class NaturezaTransacao(str, Enum):
    PF = 'pf'
    PJ = 'pj'


class TipoPagamento(str, Enum):
    CREDITO = 'credito'
    DEBITO = 'debito'
    PIX = 'pix'
    TRANSFERENCIA = 'transferencia'


class TransacaoBase(BaseModel):
    valor: float = Field(..., gt=0, description='Valor de transação')
    descricao: str = Field(..., min_length=1, max_length=500)
    parcelas: Optional[int] = Field(None, ge=1)
    total_parcelas: Optional[int] = Field(None, ge=1)
    data_transacao: datetime = Field(...)

    @field_validator('parcelas')
    def check_parcelas(cls, v: int, info: ValidationInfo) -> int:
        total = info.data.get('total_parcelas')
        if v is not None and total is not None and v > total:
            raise ValueError('Parcelas não podem exceder total_parcelas')
        return v


class TransacaoCreate(TransacaoBase):
    tipo: TipoTransacao
    natureza: NaturezaTransacao
    forma_pagamento: TipoPagamento

    categoria_id: Optional[int] = Field(None, description='ID da categoria')
    categoria_nome: Optional[str] = Field(None, description='Nome da categoria')

    subcategoria_id: Optional[int] = Field(None, description='ID da subcategoria')
    subcategoria_nome: Optional[str] = Field(None, description='Nome da subcategoria')

    @model_validator(mode='before')
    def check_categoria(cls, values):
        cid, cnome = values.get('categoria_id'), values.get('categoria_nome')
        if not cid and not cnome:
            raise ValueError('Informe categoria_id ou categoria_nome')
        return values

    @model_validator(mode='before')
    def check_subcategoria(cls, values):
        sid, snome = values.get('subcategoria_id'), values.get('subcategoria_nome')
        if not sid and not snome:
            raise ValueError('Informe subcategoria_id ou subcategoria_nome')
        return values


class TransacaoResponse(TransacaoBase):
    id: int
    tipo: TipoTransacao
    natureza: NaturezaTransacao
    forma_pagamento: TipoPagamento
    categoria_id: int
    subcategoria_id: int
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        orm_mode = True


class TransacaoUpdate(BaseModel):
    valor: Optional[float] = Field(None, gt=0, description='Valor da transação')
    descricao: Optional[str] = Field(None, min_length=1, max_length=500, description='Descrição da transação')
    parcela: Optional[int] = Field(None, ge=1, description='Número de parcelas')
    total_parcelas: Optional[int] = Field(None, ge=1, description='Total de parcelas')
    data_transacao: Optional[datetime] = Field(None, description='Data da transação')
    tipo: Optional[TipoTransacao] = Field(None, description='Tipo da transação')
    natureza: Optional[NaturezaTransacao] = Field(None, description='Natureza da transação')
    forma_pagamento: Optional[TipoPagamento] = Field(None, description='Forma de pagamento')

    categoria_id: Optional[int] = Field(None, description='ID da categoria')
    categoria_nome: Optional[str] = Field(None, description='Nome da categoria')

    subcategoria_id: Optional[int] = Field(None, description='ID da subcategoria')
    subcategoria_nome: Optional[str] = Field(None, description='Nome da subcategoria')
    
    @model_validator(mode="before")
    def check_categoria(cls, values: dict) -> dict:
        # Só checa se algum campo foi enviado
        if "categoria_id" in values or "categoria_nome" in values:
            cid = values.get("categoria_id")
            cnome = values.get("categoria_nome")
            if cid is None and not cnome:
                raise ValueError("Informe categoria_id ou categoria_nome")
        return values

    @model_validator(mode="before")
    def check_subcategoria(cls, values: dict) -> dict:
        # Só checa se algum campo foi enviado
        if "subcategoria_id" in values or "subcategoria_nome" in values:
            sid = values.get("subcategoria_id")
            snome = values.get("subcategoria_nome")
            if sid is None and not snome:
                raise ValueError("Informe subcategoria_id ou subcategoria_nome")
        return values

    class Config:
        from_attributes = True