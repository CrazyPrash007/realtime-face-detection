"""
Shared pytest fixtures.

Audit fix #6: uses AsyncClient with ASGITransport (the correct httpx pattern
for FastAPI async testing). asyncio_mode=auto in pytest.ini means no
@pytest.mark.asyncio decorators are needed on individual tests.

The database is overridden with an in-memory SQLite engine so tests are
fully self-contained and require no running PostgreSQL instance.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Must import app after patching DB so the override takes effect
from backend.db.database import Base, get_db
from backend.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite async engine (no PostgreSQL required for tests)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """Replace the real PostgreSQL session with an in-memory SQLite session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
async def setup_db():
    """Create all tables in the in-memory DB once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """
    Async HTTP test client wired to the FastAPI app.
    Audit fix #6: uses ASGITransport (not deprecated TestClient patterns).
    """
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
