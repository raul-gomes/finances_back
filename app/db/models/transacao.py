from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
from uuid import uuid4

class TransacaoORM(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(UUID(as_uuid=True), nullable=False, default=uuid4, index=True)
    valor = Column(Float, nullable=False)
    descricao = Column(String, nullable=False)
    parcela = Column(Integer)
    total_parcelas = Column(Integer)
    data_transacao = Column(DateTime, nullable=False)
    data_criacao = Column(DateTime, server_default=func.now())
    data_atualizacao = Column(DateTime, server_default=func.now(), onupdate=func.now())
    tipo = Column(String, nullable=False)
    natureza = Column(String, nullable=False)
    forma_pagamento = Column(String, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    subcategoria_id = Column(Integer, ForeignKey("subcategorias.id"), nullable=False)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    subcategoria_id = Column(Integer, ForeignKey("subcategorias.id"), nullable=False)

    categoria = relationship("CategoriaORM", lazy="joined")
    subcategoria = relationship("SubcategoriaORM", lazy="joined")
