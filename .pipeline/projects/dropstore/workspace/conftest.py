import sys, pathlib
import asyncio
import pytest

# Injected by pipeline validator — ensures local imports work in pytest
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from backend.utils.database import engine, Base


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all database tables and seed initial data before tests run."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        # Seed niches so niche_service tests can find data
        from backend.services.niche_service import seed_niches
        await seed_niches()

    loop.run_until_complete(_setup())
    yield
    loop.close()
