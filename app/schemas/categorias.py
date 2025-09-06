from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Subcategoria(BaseModel):
    subcategoria_nome: str = Field(..., description='Nome da subcategoria')

class SubcategoriaUpdate(Subcategoria):
    id: Optional[int] = None

    class Config:
        orm_mode = True

class CategoriaCreate(BaseModel):
    categoria_nome: str = Field(..., description='Nome da categoria')
    natureza: Literal['pj', 'pf', 'all'] = Field(..., description='Natureza da categoria: "pf" para pessoa física ou "pj" para pessoa jurídica')
    limite: float = Field(..., ge=0, description='Limite associado à categoria')
    subcategorias: List[Subcategoria] = Field(default_factory=list, description='Lista de subcategorias')

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

class Categoria(BaseModel):
    id: str = Field(..., description='ID da categoria')
    categoria_nome: str = Field(..., description='Nome da categoria')
    natureza: Literal['pf', 'pj', 'all'] = Field(
        ...,
        description='Natureza da categoria: "pf" para pessoa física ou "pj" para pessoa jurídica'
    )
    limite: float = Field(..., ge=0, description='Limite associado à categoria')
    subcategorias: List[Subcategoria] = Field(..., description='Lista de subcategorias')



class CategoriaUpdate(BaseModel):
    categoria_nome: Optional[str]
    natureza: Optional[Literal['pj','pf','all']]
    limite: Optional[float]
    subcategorias: List[SubcategoriaUpdate] = []

    class Config:
        orm_mode = True