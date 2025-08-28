from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date, datetime
from bson import ObjectId
from enum import Enum

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

class Transacao(BaseModel):
    tipo: TipoTransacao = Field(..., description='Tipo da transacao: entrada ou saida')
    valor: float = Field(..., gt=0, description='Valor de transacao (deve ser positivo)')
    descricao: str = Field(..., min_length=1, max_length=500, description='Descrição da transação')
    categoria: str = Field(..., min_length=1, max_length=100, description='Categoria da transação')
    subcategoria: str = Field(..., min_length=1, max_length=100, description='Subcategoria da transação')
    forma_pagamento: TipoPagamento = Field(..., description='Forma de pagamento')
    e_parcelado: bool = Field(False, description='Se é parcelado ou não')
    parcelas: Optional[int] = Field(None, ge=1, description='Quantidade de parcelas, se aplicável')
    total_parcelas: Optional[int] = Field(None, ge=1, description='Total de parcelas, se aplicável')
    natureza_transacao: NaturezaTransacao = Field(..., description='Natureza da transação')
    data_transacao: datetime = Field(..., description='Data da transação')

    @field_validator('data_transacao', mode='before')
    @classmethod
    def validate_data_transacao(cls, v) -> datetime:
        """
        Converte string DD/MM/YYYY ou outros formatos para datetime
        Aceita também datetime, date ou timestamp
        """
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        
        if isinstance(v, str):
            # Tenta formato DD/MM/YYYY primeiro
            try:
                return datetime.strptime(v, '%d/%m/%Y')
            except ValueError:
                pass
            
            # Tenta formato ISO (YYYY-MM-DD)
            try:
                return datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                pass
            
            # Tenta formato americano (MM/DD/YYYY)
            try:
                return datetime.strptime(v, '%m/%d/%Y')
            except ValueError:
                pass
            
            # Tenta formato com horário
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
            
            raise ValueError(
                'Data deve estar no formato DD/MM/YYYY, YYYY-MM-DD ou ISO format'
            )
        
        if isinstance(v, (int, float)):
            # Assume timestamp Unix
            return datetime.fromtimestamp(v)
        
        raise ValueError('Formato de data não suportado')
    

    @field_validator('parcelas')
    @classmethod
    def validate_parcelas(cls, v:Optional[int], info) -> Optional[int]:
        """Valida se parcelas não excede total_parcelas"""
        if v is not None and 'total_parcelas' in info.data:
            total_parcelas = info.data['total_parcelas']
            if v > total_parcelas:
                raise ValueError('Parcelas não pode ser maior que o total de parcelas')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "entrada",
                "valor": 123.10,
                "descricao": "Pagamento cliente XYZ",
                "categoria": "alimentação",
                "subcategoria": "restaurante",
                "forma_pagamento": "credito",
                "parcelas": 1,
                "total_parcelas": 10,
                "natureza_transacao": "pj",
                "data_transacao": "07/08/2025"
            }
        }

class TransacaoResponse(Transacao):
    id: str = Field(..., description='Id único da transação')
    data_transacao: datetime = Field(..., description='Data da criação do registro')
    data_atualizacao: datetime = Field(..., description='Data da ultima atualização')

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }


# Modelo para filtros de busca por data
class FiltroData(BaseModel):
    data_inicio: Optional[datetime] = Field(None, description="Data inicial para filtro")
    data_fim: Optional[datetime] = Field(None, description="Data final para filtro")
    
    @field_validator('data_inicio', 'data_fim', mode='before')
    @classmethod
    def validate_datas(cls, v) -> Optional[datetime]:
        """Aplica a mesma validação de data"""
        if v is None:
            return None
        
        if isinstance(v, datetime):
            return v
            
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%d/%m/%Y')
            except ValueError:
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    raise ValueError('Data deve estar no formato DD/MM/YYYY ou YYYY-MM-DD')
        
        raise ValueError('Formato de data inválido')
    
# No final do arquivo models/transacao.py

class TransacaoUpdate(Transacao):
    """Modelo para atualização - herda de Transacao mas com campos opcionais"""
    
    # Redefine todos os campos como opcionais
    tipo: Optional[TipoTransacao] = None
    valor: Optional[float] = Field(None, gt=0)
    descricao: Optional[str] = Field(None, min_length=1, max_length=500)
    categoria: Optional[str] = Field(None, min_length=1, max_length=100)
    subcategoria: Optional[str] = Field(None, min_length=1, max_length=100)
    forma_pagamento: Optional[TipoPagamento] = None
    e_parcelado: Optional[bool] = None
    parcelas: Optional[int] = Field(None, ge=1)
    total_parcelas: Optional[int] = Field(None, ge=1)
    natureza_transacao: Optional[NaturezaTransacao] = None
    data_transacao: Optional[datetime] = None
    

