import pathlib

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base

path = pathlib.Path(__file__).parent.absolute()


prod_uri = "postgresql+asyncpg://postgres:ronny@postgres:5432"
development_uri = "postgresql+asyncpg://postgres:ronny@localhost:5432"


engine: AsyncEngine = create_async_engine(prod_uri, echo=False, pool_size=1000)

SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    future=True,
    class_=AsyncSession,
    expire_on_commit=False,
)

metadata_obj = MetaData()
Base = declarative_base()


async def init_db():
    print("trying to create tables")
    try:
        async with engine.begin() as conn:
            print("creating tables")
            await conn.run_sync(Base.metadata.create_all)
            return True
    except Exception as e:
        print(e)
        return False
