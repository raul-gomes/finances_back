from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .config import Config
from app.db.base import Base

engine = create_async_engine(Config.DATABASE_URL, future=True, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = create_engine(
    Config.DATABASE_URL.replace('+aiosqlite', ''),  # usa sqlite:///
    echo=False,
    future=True,
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session