from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from src.utils.custom_app_exception import CustomAppException
from settings import config
from src.utils.helper import logger

class Database:
    def __init__(self):
        self.DATABASE_URL = (
            f"postgresql+asyncpg://{config.db_username}:{config.db_password}"
            f"@{config.db_host}:{config.db_port}/{config.db_name}"
        )
        
        
        self.engine = create_async_engine(
            self.DATABASE_URL,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True # to check connection in the pool alive , if not creates connection and sends to application
            
        )

        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        logger.info("Initiallized Database with url,engine and session ...")
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Optimized dependency using yield. 
        Ensures the session is closed after the request is finished.

        """
        async with self.SessionLocal() as session:
            try:
                logger.info('session is yielded...')
                yield session
            except Exception as e:
                await session.rollback()
                logger.info("Error in Database Initialization ...")
                raise CustomAppException(
                    message=f"Database error: {str(e)}",
                    err_code="DATABASE_INIT_ERROR",
                    status_code=500
                )
            finally:
                await session.close()

Base = declarative_base()
def get_database():
    # return Exception("hello world")
    return Database()