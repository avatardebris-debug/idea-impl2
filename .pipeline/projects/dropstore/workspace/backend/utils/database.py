"""Database utilities."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# SQLite for development, PostgreSQL for production
DATABASE_URL = "sqlite+aiosqlite:///./dropstore.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Initialize database tables."""
    import backend.models.product  # Import models to register them
    import backend.models.supplier
    import backend.models.sync_log
    import backend.models.margin_rule
    import backend.models.alert
    from sqlalchemy import inspect
    
    async with engine.begin() as conn:
        # Create all tables
        from backend.models.product import Niche, Product, Catalog, CatalogProduct, ShopifyStore, SyncJob
        from backend.models.supplier import SupplierConnection, SupplierProduct
        from backend.models.sync_log import SyncLog
        from backend.models.margin_rule import MarginRule
        from backend.models.alert import Alert
        await conn.run_sync(Base.metadata.create_all)


async def seed_database():
    """Seed database with initial data."""
    from backend.services.niche_service import seed_niches
    count = await seed_niches()
    return count
