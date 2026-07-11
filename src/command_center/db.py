from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")
        async with self.pool.acquire() as connection:
            yield connection
