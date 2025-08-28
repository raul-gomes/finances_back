from pydantic import BaseModel, Field
from typing import List

class Subcategoria(BaseModel):
    subcategoria_nome: str = Field(..., description='Nome da subcategoria')

class CategoriaCreate(BaseModel):
    categoria_nome: str = Field(..., description='Nome da categoria')
    limite: float = Field(..., ge=0, description='Limite associado à categoria')
    subcategorias: List[str] = Field(default_factory=list, description='Lista de subcategorias')

    class Config:
        json_schema_extra = {
            "example": {
                "categoria_nome": "Marketing",
                "limite": 5000.00,
                "subcategorias": [
                    "Google Ads",
                    "Facebook Ads",
                    "Design Gráfico"
                ]
            }
        }

class Categoria(BaseModel):
    id: str = Field(..., description='ID da categoria')
    categoria_nome: str = Field(..., description='Nome da categoria')
    limite: float = Field(..., ge=0, description='Limite associado à categoria')
    subcategorias: List[Subcategoria] = Field(..., description='Lista de subcategorias')