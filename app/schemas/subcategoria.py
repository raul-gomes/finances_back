from pydantic import BaseModel, Field
from typing import Optional

class SubcategoriaBase(BaseModel):
    subcategoria_nome: str = Field(..., description="Nome da subcategoria")

class Subcategoria(SubcategoriaBase):
    id: int = Field(..., description="ID da subcategoria")  # int em vez de str

    class Config:
        orm_mode = True

class SubcategoriaCreate(SubcategoriaBase):
    """Schema para criar subcategorias (sem id)"""
    pass

class SubcategoriaUpdate(SubcategoriaBase):
    id: Optional[int] = Field(None, description="ID da subcategoria existente")

    class Config:
        orm_mode = True
