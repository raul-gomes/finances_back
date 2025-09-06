from sqlalchemy import (
    Column, Integer, Float, String, Boolean,
    DateTime, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.base import Base

class TipoTransacaoEnum(Enum):
    ENTRADA = 'entrada'
    SAIDA = 'saida'
    INVESTIMENTO = 'investimento'

class NaturezaTransacaoEnum(Enum):
    PF = 'pf'
    PJ = 'pj'

class TipoPagamentoEnum(Enum):
    CREDITO = 'credito'
    DEBITO = 'debito'
    PIX = 'pix'
    TRANSFERENCIA = 'transferencia'
    DINHEIRO = 'dinheiro'


class TransacaoORM(Base):
    __tablename__ = 'transacoes'

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    descricao = Column(String(500), nullable=False)
    parcela = Column(Integer, nullable=True)
    total_parcelas = Column(Integer, nullable=True)
    data_transacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tipo = Column(SQLEnum(TipoTransacaoEnum), nullable=False)
    natureza_transacao = Column(SQLEnum(NaturezaTransacaoEnum), nullable=False)
    forma_pagamento = Column(SQLEnum(TipoPagamentoEnum), nullable=False)
    categoria_id = Column(Integer, ForeignKey('categorias.id'), nullable=False)
    subcategoria_id = Column(Integer, ForeignKey('subcategorias.id'), nullable=False)

    categoria = relationship('CategoriaORM', lazy='joined')
    subcategoria = relationship('SubcategoriaORM', lazy='joined')