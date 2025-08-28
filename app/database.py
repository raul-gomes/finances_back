from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from .logger import logger, log_database_operation
from .config import Config

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    '''Conecta ao mongo async com PyMongo 4.x+'''
    db_logger = log_database_operation('connect', database=Config.DATABASE_NAME)
    
    try:
        db_logger.info('Iniciando conexão com mongoDB')
        db_logger.debug(f'Database: {Config.DATABASE_NAME}')
        db_logger.debug(f'URL: {Config.MONGODB_URL}')

        # Cria cliente async
        mongodb.client = AsyncIOMotorClient(Config.MONGODB_URL)
        mongodb.database = mongodb.client[Config.DATABASE_NAME]
        
        # Comando ping async
        await mongodb.client.admin.command("ping")
        db_logger.info("Conectado ao MongoDB com sucesso")
    except PyMongoError as e:
        db_logger.error(f"Erro ao conectar ao mongodb: {e}")
        raise
    except Exception as e:
        db_logger.error(f'Erro inesperado ao conectar: {e}')

async def close_mongo_connection():
    '''Fecha conexão async com MongoDB'''
    if mongodb.client:
        mongodb.client.close()
        logger.info("Conexão com MongoDB fechada")

def get_database():
    return mongodb.database
