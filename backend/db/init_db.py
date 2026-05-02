from backend.db.database import Base, engine


async def create_tables() -> None:
    """Create all database tables on application startup (idempotent)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
