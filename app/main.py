from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from .core.database import connect_to_mongo, close_mongo_connection
from .logger import logger, log_with_context

from .routes.transacoes_routes import router as trasacoes_router
from .routes.categorias_routes import router as categorias_router
from .routes.dashboard_routes import router as dashboard_router
from .routes.limits_routes import router as limits_router

app = FastAPI(
    title="API Financeira",
    description='API para gerenciamento de transações financeiras',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["http://localhost:8080", "http://172.25.208.1:8080", "http://172.17.160.1:8080", "http://192.168.15.2:8080/"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trasacoes_router)
app.include_router(categorias_router)
app.include_router(dashboard_router)
app.include_router(limits_router)

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