import os
from dotenv import load_dotenv
from .db_models import Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    await engine.dispose()

async def get_db():
    async with SessionLocal() as db:
        yield db