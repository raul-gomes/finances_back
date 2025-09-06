from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date, datetime
from bson import ObjectId
from enum import Enum

from app.schemas.categorias import Categoria, Subcategoria

class TipoTransacao(str, Enum):
    ENTRADA = 'entrada'
    SAIDA = 'saida'

class NaturezaTransacao(str, Enum):
    PF = 'pf'
    PJ = 'pj'

class TipoPagamento(str, Enum):
    CREDITO = 'credito'
    DEBITO = 'debito'
    PIX = 'pix'
    TRANSFERENCIA = 'transferencia'

class TransacaoBase(BaseModel):
    valor: float = Field(..., gt=0, description='Valor de transacao (deve ser positivo)')
    descricao: str = Field(..., min_length=1, max_length=500, description='Descrição da transação')
    parcelas: Optional[int] = Field(None, ge=1, description='Quantidade de parcelas, se aplicável')
    total_parcelas: Optional[int] = Field(None, ge=1, description='Total de parcelas, se aplicável')
    data_transacao: datetime = Field(..., description='Data da transação')
    
    @field_validator('parcelas')
    def check_parcelas(cls, v, values):
        total = values.get('total_parcelas')
        if v is not None and total is not None and v > total:
            raise ValueError('Parcelas não podem execeder total de parcelas')
        return v
    

class TransacaoCreate(TransacaoBase):
    tipo: TipoTransacao
    natureza: NaturezaTransacao
    forma_pagamento: TipoPagamento
    categoria_id: int
    subcategoria_id: int



class TransacaoResponse(TransacaoBase):
    id: int
    tipo: TipoTransacao
    natureza: NaturezaTransacao
    forma_pagamento: TipoPagamento
    categoria: Categoria
    subcategoria: Subcategoria
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        orm_mode = True