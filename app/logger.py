# app/logger.py
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime

def setup_logger(app_name: str = "financas_backend"):
    """
    Configura o Loguru uma única vez para todo o projeto
    """
    
    # Remove handlers padrão
    logger.remove()
    
    # Cria diretório de logs
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Formato para console (colorido e limpo)
    console_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Formato para arquivo (mais detalhado)
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{extra} | "
        "{message}"
    )
    
    # Console handler
    logger.add(
        sys.stdout,
        format=console_format,
        level="DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Arquivo geral
    logger.add(
        logs_dir / f"{app_name}.log",
        format=file_format,
        level="DEBUG",
        rotation="50 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    # Arquivo só para erros
    logger.add(
        logs_dir / f"{app_name}_errors.log",
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="90 days",
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    # Logs estruturados em JSON
    logger.add(
        logs_dir / f"{app_name}_structured.json",
        format="{message}",
        level="INFO",
        serialize=True,  # Formato JSON
        rotation="25 MB",
        retention="30 days",
        encoding="utf-8"
    )
    
    logger.info(f"Logger configurado para {app_name}")
    return logger

# Configura o logger na importação
setup_logger()

# Função para adicionar contexto
def log_with_context(**kwargs):
    """
    Adiciona contexto específico aos logs
    Exemplo: log_with_context(user_id="123", request_id="abc")
    """
    return logger.bind(**kwargs)

# Função para logs de operações de banco
def log_database_operation(operation: str, collection: str = None, **context):
    """
    Log específico para operações de banco
    """
    return logger.bind(
        operation=operation,
        collection=collection,
        **context
    )

# Função para logs de API requests
def log_api_request(method: str, endpoint: str, **context):
    """
    Log específico para requests de API
    """
    return logger.bind(
        http_method=method,
        endpoint=endpoint,
        **context
    )
