# app/config/database.py

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from sqlalchemy.orm import declarative_base

from app.config.settings import settings


# =========================================================
# DATABASE ENGINE
# =========================================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)


# =========================================================
# SESSION FACTORY
# =========================================================
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =========================================================
# BASE MODEL
# =========================================================
Base = declarative_base()


# =========================================================
# DATABASE DEPENDENCY
# =========================================================
async def get_db():

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# =========================================================
# INIT DATABASE
# =========================================================
async def init_db():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database initialized")


# =========================================================
# HEALTH CHECK
# =========================================================
async def check_db_connection():

    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")

        return True

    except Exception as e:
        print(f"Database connection failed: {e}")
        return False