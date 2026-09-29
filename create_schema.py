import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sourceai.storage.models import Base
from sourceai.config.settings import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Schema created. Tables:", sorted(Base.metadata.tables.keys()))

asyncio.run(main())
