from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import connect_to_mongo, close_mongo_connection
from .logger import logger, log_with_context

from .routes.transacoes_routes import router as trasacoes_router
from .routes.categorias_routes import router as categorias_router
from .routes.dashboard_routes import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''Gerencia o ciclo de vida da aplicação'''
    startup_logger = log_with_context(event='startup')
    startup_logger.info('Iniciando aplicação FastAPI')
    try:
        await connect_to_mongo()
        startup_logger.success('Aplicação iniciada com sucesso')
        yield
    except Exception as e:
        startup_logger.error(f'Erro no startup {e}')
    finally:
        shutdown_logger = log_with_context(event='shutdown')
        shutdown_logger.info('Encerrando a aplicação')
        await close_mongo_connection()
        shutdown_logger.info('Aplicação encerrada')



app = FastAPI(
    title="API Financeira",
    description='API para gerenciamento de transações financeiras',
    version='1.0.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trasacoes_router)
app.include_router(categorias_router)
app.include_router(dashboard_router)

@app.get('/', tags=['Root'])
async def root():
    '''Endpoint raiz da api'''
    logger.info('Endpoint inicializado')
    return {
        'message': 'API Financeira está funcionando!',
        'docs': '/docs',
        'redoc': '/redoc'
    }

@app.get('/health', tags=['Health'])
async def health():
    '''Health check geral da api'''
    return {
        'status': 'Healthy',
        'service': 'api-financeira'
    }