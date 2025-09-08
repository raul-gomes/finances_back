# app/schemas/categoria.py

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

from app.schemas.subcategoria import Subcategoria, SubcategoriaCreate, SubcategoriaUpdate


class CategoriaBase(BaseModel):
    categoria_nome: str = Field(..., description='Nome da categoria')
    natureza: Literal['pj', 'pf', 'all'] = Field(..., description='Natureza da categoria')
    limite: float = Field(..., ge=0, description='Limite associado à categoria')

class CategoriaCreate(CategoriaBase):
    subcategorias: List[SubcategoriaCreate] = Field(default_factory=list, description='Lista de subcategorias')

    class Config:
        json_schema_extra = {
            "example": {
                "categoria_nome": "Marketing",
                "natureza": "pj",
                "limite": 5000.00,
                "subcategorias": [
                    {"subcategoria_nome": "Google Ads"},
                    {"subcategoria_nome": "Facebook Ads"},
                    {"subcategoria_nome": "Design Gráfico"}
                ]
            }
        }

class Categoria(CategoriaBase):
    id: int = Field(..., description='ID da categoria')  # Mudança: int em vez de str
    subcategorias: List[Subcategoria] = Field(..., description='Lista de subcategorias')

    class Config:
        orm_mode = True

class CategoriaUpdate(BaseModel):
    categoria_nome: Optional[str] = None
    natureza: Optional[Literal['pj','pf']] = None
    limite: Optional[float] = None
    subcategorias: Optional[List[SubcategoriaUpdate]] = Field(default=None)

    class Config:
        orm_mode = True
