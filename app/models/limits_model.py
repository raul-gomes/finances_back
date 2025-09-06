from typing import List
from pydantic import BaseModel, Field, RootModel


class Subcategory(BaseModel):
    id: str
    subcategoria_nome: str


class Category(BaseModel):
    id: str
    categoria_nome: str
    natureza: str
    limite: float
    subcategorias: List[Subcategory] = Field(default_factory=list)


class LimitsResponse(RootModel[List[Category]]):
    pass
    
    # Permite acessar lista com limits_response.__root__
