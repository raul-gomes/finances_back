# app/routes/transacoes.py

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.logger import log_api_request, log_with_context
from app.models.categorias_model import CategoriaCreate
from ..models.transacoes_model import (
    Transacao,
    TransacaoResponse,
    TransacaoUpdate
)

router = APIRouter(prefix='/transacoes', tags=['Transações'])


async def get_transacoes_collection():
    '''Dependency para obter a collection de transações do MongoDB.'''
    db = get_database()
    return db.transacoes

async def get_categorias_collection():
    '''Dependency para obter a collection de categorias.'''
    return get_database().categorias


@router.get(
    '/',
    response_model=List[TransacaoResponse],
    status_code=status.HTTP_200_OK,
    summary='Listar todas as transações',
    description='Retorna lista de todas as transações cadastradas, ordenadas por data.'
)
async def listar_transacoes(
    transacoes_col=Depends(get_transacoes_collection)
) -> List[TransacaoResponse]:
    '''
    Lista todas as transações financeiras.
    
    - **transacoes_col**: coleção de transações via Depends.
    - Retorna lista de TransacaoResponse ordenada por data_transacao desc.
    '''
    api_logger = log_api_request('GET', '/transacoes')
    api_logger.info('Listando todas as transações')

    docs = await transacoes_col.find().sort('data_transacao', -1).to_list(length=None)
    transacoes = []
    for doc in docs:
        doc['id'] = str(doc.pop('_id'))
        transacoes.append(TransacaoResponse(**doc))

    api_logger.success('Total de transações retornadas', count=len(transacoes))
    return transacoes

@router.get(
    '/{transacao_id}',
    response_model=TransacaoResponse,
    summary='Buscar transação por ID',
    description='Retorna uma transação específica pelo seu ID'
)
async def buscar_transacao_por_id(
    transacao_id: str,
    collection=Depends(get_transacoes_collection)
) -> TransacaoResponse:
    '''
    Busca uma transação financeira pelo identificador único.

    - **transacao_id**: ID da transação na URL.
    - **collection**: injeção da coleção de transações via Depends.
    - Retorna a transação encontrada (TransacaoResponse).
    - Gera erro 400 se o ID for inválido, 404 se não encontrado.
    '''
    api_logger = log_api_request('GET', f'/transacoes/{transacao_id}', transaction_id=transacao_id)
    try:
        api_logger.info('Buscando transação no banco')
        if not ObjectId.is_valid(transacao_id):
            api_logger.warning('ID inválido fornecido', transaction_id=transacao_id)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'ID de transação inválido')

        transacao = await collection.find_one({'_id': ObjectId(transacao_id)})
        if not transacao:
            api_logger.warning('Transação não encontrada', transaction_id=transacao_id)
            raise HTTPException(status.HTTP_404_NOT_FOUND, 'Transação não encontrada')

        transacao['id'] = str(transacao.pop('_id'))
        api_logger.success('Transação retornada com sucesso', transaction_id=transacao['id'])
        return TransacaoResponse(**transacao)

    except HTTPException:
        raise
    except Exception as e:
        api_logger.exception('Erro interno ao buscar transação', error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Erro interno do servidor')

@router.post(
    '/',
    response_model=TransacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Cadastrar nova transação',
    description='Cria uma nova transação financeira, auto-criando categoria/subcategoria se necessário.'
)
async def criar_transacao(
    transacao: Transacao,
    transacoes_col=Depends(get_transacoes_collection),
    categorias_col=Depends(get_categorias_collection)
) -> TransacaoResponse:
    '''
    Cadastra uma nova transação financeira.
    
    - **transacao**: dados da transação no corpo da requisição.
    - **transacoes_col**: coleção de transações via Depends.
    - **categorias_col**: coleção de categorias via Depends.
    - Se a categoria ou subcategoria não existir, cria registro em categorias.
    - Retorna TransacaoResponse com timestamps.
    '''
    api_logger = log_api_request('POST', '/transacoes')
    try:
        api_logger.info('Recebendo dados de nova transação', data=transacao.model_dump())
        now = datetime.utcnow()

        # Garantir categoria
        cat = await categorias_col.find_one({'categoria_nome': transacao.categoria})
        if not cat:
            api_logger.info('Categoria não encontrada, criando', categoria=transacao.categoria)
            nova_cat = CategoriaCreate(
                categoria_nome=transacao.categoria,
                limite=0.0,
                subcategorias=[transacao.subcategoria]
            )
            # Insere no banco usando o dict validado pelo Pydantic
            await categorias_col.insert_one(nova_cat.model_dump())
        else:
            if transacao.subcategoria not in cat.get('subcategorias', []):
                api_logger.info('Subcategoria não encontrada, adicionando',
                                categoria=transacao.categoria,
                                subcategoria=transacao.subcategoria)
                await categorias_col.update_one(
                    {'_id': cat['_id']},
                    {'$addToSet': {'subcategorias': transacao.subcategoria}}
                )
        
        tx = transacao.model_dump()
        tx.update({
            'data_transacao': now,
            'data_atualizacao': now
        })

        result = await transacoes_col.insert_one(tx)
        api_logger.debug('Resultado insert_one', acknowledged=result.acknowledged,
                         inserted_id=str(result.inserted_id))

        if not result.acknowledged:
            api_logger.error('Falha ao inserir transação')
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Falha ao inserir')

        created = await transacoes_col.find_one({'_id': result.inserted_id})
        if not created:
            api_logger.error('Transação não encontrada após criação')
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                'Transação não encontrada após criação')

        created['id'] = str(created.pop('_id'))
        api_logger.success('Transação criada com sucesso', transaction_id=created['id'])
        return TransacaoResponse(**created)

    except HTTPException:
        api_logger.warning('HTTPException durante criação de transação')
        raise
    except Exception as e:
        api_logger.exception('Erro interno ao criar transação', error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Erro interno do servidor')

@router.put(
    '/{transacao_id}',
    response_model=TransacaoResponse,
    summary='Atualizar transação',
    description='Atualiza uma transação existente'
)
async def atualizar_transacao(
    transacao_id: str,
    transacao_update: TransacaoUpdate,
    collection=Depends(get_transacoes_collection)
) -> TransacaoResponse:
    '''
    Atualiza campos de uma transação existente.

    - **transacao_id**: ID da transação na URL.
    - **transacao_update**: dados de atualização no corpo da requisição (TransacaoUpdate).
    - **collection**: injeção da coleção de transações via Depends.
    - Retorna a transação atualizada (TransacaoResponse).
    - Gera erro 400 se ID inválido ou sem campos válidos, 404 se não encontrada.
    '''
    api_logger = log_api_request('PUT', f'/transacoes/{transacao_id}', transaction_id=transacao_id)
    try:
        api_logger.info('Iniciando atualização de transação', update_data=transacao_update.model_dump())
        if not ObjectId.is_valid(transacao_id):
            api_logger.warning('ID inválido para atualização', transaction_id=transacao_id)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'ID de transação inválido')

        existente = await collection.find_one({'_id': ObjectId(transacao_id)})
        if not existente:
            api_logger.warning('Transação não encontrada para atualização', transaction_id=transacao_id)
            raise HTTPException(status.HTTP_404_NOT_FOUND, 'Transação não encontrada')

        update_data = transacao_update.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            api_logger.warning('Nenhum campo válido para atualização', transaction_id=transacao_id)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Nenhum campo válido fornecido para atualização')

        update_data['data_atualizacao'] = datetime.utcnow()
        result = await collection.update_one(
            {'_id': ObjectId(transacao_id)},
            {'$set': update_data}
        )
        api_logger.debug('Resultado update_one', matched_count=result.matched_count, modified_count=result.modified_count)

        updated = await collection.find_one({'_id': ObjectId(transacao_id)})
        updated['id'] = str(updated.pop('_id'))
        api_logger.success('Transação atualizada com sucesso', transaction_id=updated['id'])
        return TransacaoResponse(**updated)

    except HTTPException:
        raise
    except Exception as e:
        api_logger.exception('Erro interno ao atualizar transação', error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Erro interno do servidor')

@router.delete(
    '/{transacao_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Remover transação',
    description='Remove uma transação existente pelo ID'
)
async def remover_transacao(
    transacao_id: str,
    collection=Depends(get_transacoes_collection)
):
    '''
    Remove uma transação financeira pelo identificador único.

    - **transacao_id**: ID da transação na URL.
    - **collection**: injeção da coleção de transações via Depends.
    - Retorna status 204 (No Content) em caso de sucesso.
    - Gera erro 400 se ID inválido, 404 se não encontrada.
    '''
    api_logger = log_api_request('DELETE', f'/transacoes/{transacao_id}', transaction_id=transacao_id)
    try:
        api_logger.info('Iniciando remoção de transação')
        if not ObjectId.is_valid(transacao_id):
            api_logger.warning('ID inválido para remoção', transaction_id=transacao_id)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'ID de transação inválido')

        existente = await collection.find_one({'_id': ObjectId(transacao_id)})
        if not existente:
            api_logger.warning('Transação não encontrada para remoção', transaction_id=transacao_id)
            raise HTTPException(status.HTTP_404_NOT_FOUND, 'Transação não encontrada')

        result = await collection.delete_one({'_id': ObjectId(transacao_id)})
        api_logger.debug('Resultado delete_one', deleted_count=result.deleted_count)

        if result.deleted_count == 0:
            api_logger.error('Falha ao remover transação', transaction_id=transacao_id)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Falha ao remover transação')

        api_logger.success('Transação removida com sucesso', transaction_id=transacao_id)
        return

    except HTTPException:
        raise
    except Exception as e:
        api_logger.exception('Erro interno ao remover transação', error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Erro interno do servidor')
