from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Any, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

T = TypeVar("T", bound=BaseModel)


class Record(BaseModel):
    """Base class for all records, inherits from Pydantic v2 BaseModel."""

    pass


class Connection:
    def __init__(self, conn: SAConnection):
        self._conn = conn

    async def query(self, query: str, **params) -> Any:
        result = await self._conn.execute(text(query), params)
        return result

    async def fetch_all(self, query: str, model: Type[T], **params) -> List[T]:
        result = await self._conn.execute(text(query), params)
        rows = result.fetchall()
        return [model(**row._mapping) for row in rows]

    async def fetch_one(self, query: str, model: Type[T], **params) -> Optional[T]:
        result = await self._conn.execute(text(query), params)
        row = result.fetchone()
        if row:
            return model(**row._mapping)
        return None

    async def bulk_query(self, query: str, values: Sequence[dict]) -> Any:
        result = await self._conn.execute(text(query), values)
        return result

    async def query_file(self, path: str, **params) -> Any:
        async with await self._conn._handle.dbapi_connection.cursor() as cursor:
            with open(path) as f:
                sql = f.read()
            result = await self._conn.execute(text(sql), params)
            return result

    async def bulk_query_file(self, path: str, values: Sequence[dict]) -> Any:
        with open(path) as f:
            sql = f.read()
        result = await self._conn.execute(text(sql), values)
        return result

    async def get_table_names(self) -> List[str]:
        inspector = inspect(self._conn)
        return await inspector.get_table_names()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator["Connection", None]:
        trans = await self._conn.begin()
        try:
            yield self
            await trans.commit()
        except Exception:
            await trans.rollback()
            raise

    async def close(self):
        await self._conn.close()


class Database:
    def __init__(self, db_url: str):
        self._engine: AsyncEngine = create_async_engine(db_url, future=True)

    async def connect(self) -> Connection:
        conn = await self._engine.connect()
        return Connection(conn)

    async def close(self):
        await self._engine.dispose()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection, None]:
        conn = await self._engine.connect()
        trans = await conn.begin()
        connection = Connection(conn)
        try:
            yield connection
            await trans.commit()
        except Exception:
            await trans.rollback()
            raise
        finally:
            await conn.close()

    async def query_file(self, path: str, **params) -> Any:
        conn = await self.connect()
        try:
            return await conn.query_file(path, **params)
        finally:
            await conn.close()

    async def bulk_query_file(self, path: str, values: Sequence[dict]) -> Any:
        conn = await self.connect()
        try:
            return await conn.bulk_query_file(path, values)
        finally:
            await conn.close()

    async def get_table_names(self) -> List[str]:
        conn = await self.connect()
        try:
            return await conn.get_table_names()
        finally:
            await conn.close()
