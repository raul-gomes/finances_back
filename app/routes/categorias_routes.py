from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId

from app.database import get_database
from app.logger import log_api_request, log_with_context
from ..models.categorias_model import Categoria, CategoriaCreate, Subcategoria

router = APIRouter(prefix='/categorias', tags=['Categorias'])


def get_categorias_collection():
    '''Dependency para obter a collection de categorias do MongoDB.'''
    return get_database().categorias


@router.get(
    '/',
    response_model=List[Categoria],
    summary='Listar categorias',
    status_code=status.HTTP_200_OK
)
async def listar_categorias(
    collection=Depends(get_categorias_collection)
) -> List[Categoria]:
    '''
    Lista todas as categorias cadastradas no sistema.

    - **collection**: injeção da coleção de categorias via Depends.
    - Retorna lista de objetos Categoria.
    '''
    api_logger = log_api_request('GET', '/categorias')
    api_logger.info('Listando todas as categorias')
    
    docs = await collection.find().to_list(None)
    categorias = [
        Categoria(
            id=str(doc['_id']),
            categoria_nome=doc['categoria_nome'],
            limite=doc['limite'],
            subcategorias=[
                Subcategoria(subcategoria_nome=s)
                for s in doc.get('subcategorias', [])
            ]
        )
        for doc in docs
    ]
    
    api_logger.success(f'{len(categorias)} categorias listadas')
    return categorias

@router.get(
    '/{categoria_id}/subcategorias',
    response_model=List[Subcategoria],
    status_code=status.HTTP_200_OK,
    summary='Listar subcategorias',
    description='Retorna todas as subcategorias de uma categoria específica.'
)
async def listar_subcategorias(
    categoria_id: str,
    collection=Depends(get_categorias_collection)
) -> List[Subcategoria]:
    """
    Lista todas as subcategorias de uma categoria.

    - **categoria_id**: ID da categoria na URL.
    - **collection**: injeção da coleção de categorias via Depends.
    - Retorna lista de objetos Subcategoria.
    - Gera erro 400 se o ID for inválido, 404 se a categoria não for encontrada.
    """
    api_logger = log_api_request(
        'GET',
        f'/categorias/{categoria_id}/subcategorias'
    )
    api_logger.info('Listando subcategorias', category_id=categoria_id)

    if not ObjectId.is_valid(categoria_id):
        api_logger.warning('ID de categoria inválido', category_id=categoria_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'ID inválido')

    cat = await collection.find_one({'_id': ObjectId(categoria_id)})
    if not cat:
        api_logger.error('Categoria não encontrada', category_id=categoria_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Categoria não encontrada')

    subs = cat.get('subcategorias', [])
    api_logger.success('Subcategorias listadas com sucesso',
                       category_id=categoria_id,
                       count=len(subs))
    return [Subcategoria(subcategoria_nome=s) for s in subs]

@router.post(
    '/',
    response_model=Categoria,
    status_code=status.HTTP_201_CREATED,
    summary='Criar categoria',
    description='Cria uma nova categoria com suas subcategorias.'
)
async def criar_categoria(
    payload: CategoriaCreate,
    collection=Depends(get_categorias_collection)
) -> Categoria:
    '''
    Cria uma nova categoria financeira.

    - **payload**: dados da categoria no corpo da requisição (CategoriaCreate).
    - **collection**: injeção da coleção de categorias via Depends.
    - Retorna a categoria criada (Categoria).
    '''
    api_logger = log_api_request('POST', '/categorias')
    api_logger.info('Criando categoria', data=payload.model_dump())
    
    doc = CategoriaCreate(
                categoria_nome=payload.categoria,
                limite=0.0,
                subcategorias=[payload.subcategoria]
            )
    result = await collection.insert_one(doc)
    api_logger.debug('Resultado insert_one', acknowledged=result.acknowledged, inserted_id=str(result.inserted_id))
    
    if not result.acknowledged:
        api_logger.error('Falha ao criar categoria')
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Falha ao criar categoria')

    created = await collection.find_one({'_id': result.inserted_id})
    categoria = Categoria(
        id=str(created['_id']),
        categoria_nome=created['categoria_nome'],
        limite=created['limite'],
        subcategorias=[
            Subcategoria(subcategoria_nome=s)
            for s in created.get('subcategorias', [])
        ]
    )
    api_logger.success('Categoria criada com sucesso', category_id=categoria.id)
    return categoria

@router.post(
    '/{categoria_id}/subcategorias',
    response_model=Categoria,
    summary='Adicionar subcategoria',
    description='Adiciona uma nova subcategoria a uma categoria existente.'
)
async def adicionar_subcategoria(
    categoria_id: str,
    nome: str,
    collection=Depends(get_categorias_collection)
) -> Categoria:
    '''
    Adiciona uma subcategoria a uma categoria existente.

    - **categoria_id**: ID da categoria na URL.
    - **nome**: nome da subcategoria a adicionar.
    - **collection**: injeção da coleção de categorias via Depends.
    - Retorna a categoria atualizada (Categoria).
    - Gera erro 400 se ID inválido, 404 se categoria não encontrada.
    '''
    api_logger = log_api_request(
        'POST',
        f'/categorias/{categoria_id}/subcategorias',
        category_id=categoria_id
    )
    api_logger.info('Adicionando subcategoria', subcategory=nome)

    if not ObjectId.is_valid(categoria_id):
        api_logger.warning('ID inválido para adicionar subcategoria', category_id=categoria_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'ID inválido')

    result = await collection.update_one(
        {'_id': ObjectId(categoria_id)},
        {'$addToSet': {'subcategorias': nome}}
    )
    api_logger.debug('Resultado update_one', matched_count=result.matched_count, modified_count=result.modified_count)

    if result.matched_count == 0:
        api_logger.error('Categoria não encontrada para adicionar subcategoria', category_id=categoria_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Categoria não encontrada')

    doc = await collection.find_one({'_id': ObjectId(categoria_id)})
    categoria = Categoria(
        id=str(doc['_id']),
        categoria_nome=doc['categoria_nome'],
        limite=doc['limite'],
        subcategorias=[Subcategoria(subcategoria_nome=s) for s in doc.get('subcategorias', [])]
    )
    api_logger.success('Subcategoria adicionada com sucesso', category_id=categoria.id)
    return categoria

@router.patch(
    '/{categoria_id}',
    response_model=Categoria,
    summary='Atualizar limite da categoria',
    description='Atualiza o valor de limite de uma categoria existente.'
)
async def atualizar_limite(
    categoria_id: str,
    limite: float,
    collection=Depends(get_categorias_collection)
) -> Categoria:
    '''
    Atualiza o limite de gastos de uma categoria.

    - **categoria_id**: ID da categoria na URL.
    - **limite**: novo valor de limite.
    - **collection**: injeção da coleção de categorias via Depends.
    - Retorna a categoria atualizada (Categoria).
    - Gera erro 400 se ID inválido, 404 se categoria não encontrada.
    '''
    api_logger = log_api_request(
        'PATCH',
        f'/categorias/{categoria_id}',
        category_id=categoria_id
    )
    api_logger.info('Atualizando limite da categoria', new_limit=limite)

    if not ObjectId.is_valid(categoria_id):
        api_logger.warning('ID inválido para atualização de limite', category_id=categoria_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'ID inválido')

    result = await collection.update_one(
        {'_id': ObjectId(categoria_id)},
        {'$set': {'limite': limite}}
    )
    api_logger.debug('Resultado update_one', matched_count=result.matched_count, modified_count=result.modified_count)

    if result.matched_count == 0:
        api_logger.error('Categoria não encontrada para atualização de limite', category_id=categoria_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Categoria não encontrada')

    doc = await collection.find_one({'_id': ObjectId(categoria_id)})
    categoria = Categoria(
        id=str(doc['_id']),
        categoria_nome=doc['categoria_nome'],
        limite=doc['limite'],
        subcategorias=[Subcategoria(subcategoria_nome=s) for s in doc.get('subcategorias', [])]
    )
    api_logger.success('Limite da categoria atualizado com sucesso', category_id=categoria.id)
    return categoria

@router.delete(
    '/{categoria_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Excluir categoria',
    description='Remove uma categoria e todas as suas subcategorias associadas.'
)
async def excluir_categoria(
    categoria_id: str,
    collection=Depends(get_categorias_collection)
):
    """
    Exclui uma categoria inteira pelo seu ID.
    
    - **categoria_id**: ID da categoria na URL.
    - **collection**: injeção da coleção de categorias via Depends.
    - Retorna status 204 No Content em caso de sucesso.
    - Gera erro 400 se o ID for inválido, 404 se a categoria não for encontrada.
    """
    api_logger = log_api_request('DELETE', f'/categorias/{categoria_id}')
    api_logger.info('Iniciando exclusão de categoria', category_id=categoria_id)

    if not ObjectId.is_valid(categoria_id):
        api_logger.warning('ID de categoria inválido', category_id=categoria_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'ID inválido')

    result = await collection.delete_one({'_id': ObjectId(categoria_id)})
    api_logger.debug('Resultado delete_one', deleted_count=result.deleted_count)

    if result.deleted_count == 0:
        api_logger.error('Categoria não encontrada para exclusão', category_id=categoria_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Categoria não encontrada')

    api_logger.success('Categoria excluída com sucesso', category_id=categoria_id)
    return

@router.delete(
    '/{categoria_id}/subcategorias/{subcategoria_nome}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Excluir subcategoria',
    description='Remove apenas uma subcategoria de uma categoria existente.'
)
async def excluir_subcategoria(
    categoria_id: str,
    subcategoria_nome: str,
    collection=Depends(get_categorias_collection)
):
    """
    Exclui uma única subcategoria de uma categoria.

    - **categoria_id**: ID da categoria na URL.
    - **subcategoria_nome**: nome da subcategoria a remover.
    - **collection**: injeção da coleção de categorias via Depends.
    - Retorna status 204 No Content em caso de sucesso.
    - Gera erro 400 se o ID for inválido, 404 se categoria ou subcategoria não forem encontradas.
    """
    api_logger = log_api_request(
        'DELETE',
        f'/categorias/{categoria_id}/subcategorias/{subcategoria_nome}'
    )
    api_logger.info('Iniciando exclusão de subcategoria',
                    category_id=categoria_id,
                    subcategoria=subcategoria_nome)

    if not ObjectId.is_valid(categoria_id):
        api_logger.warning('ID de categoria inválido', category_id=categoria_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'ID inválido')

    # Verifica existência da categoria
    cat = await collection.find_one({'_id': ObjectId(categoria_id)})
    if not cat:
        api_logger.error('Categoria não encontrada', category_id=categoria_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Categoria não encontrada')

    if subcategoria_nome not in cat.get('subcategorias', []):
        api_logger.error('Subcategoria não encontrada na categoria',
                         category_id=categoria_id,
                         subcategoria=subcategoria_nome)
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Subcategoria não encontrada')

    result = await collection.update_one(
        {'_id': ObjectId(categoria_id)},
        {'$pull': {'subcategorias': subcategoria_nome}}
    )
    api_logger.debug('Resultado update_one', modified_count=result.modified_count)

    api_logger.success('Subcategoria excluída com sucesso',
                       category_id=categoria_id,
                       subcategoria=subcategoria_nome)
    return