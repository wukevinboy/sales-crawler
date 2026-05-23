from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.db.models import Base

DATABASE_URL = "sqlite+aiosqlite:///./data/sales_crawler.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for col in ["summary_zh", "features_zh"]:
            try:
                await conn.execute(text(f"ALTER TABLE websites ADD COLUMN {col} TEXT"))
            except Exception:
                pass
        try:
            await conn.execute(text("ALTER TABLE analysis_reports ADD COLUMN insights_json JSON"))
        except Exception:
            pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
