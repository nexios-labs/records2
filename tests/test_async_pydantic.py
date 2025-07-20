import asyncio
import os

import pytest
from pydantic import BaseModel

from records2 import async_database

TEST_DB_URL = os.environ.get("TEST_DB_URL", "sqlite+aiosqlite:///:memory:")


class User(BaseModel):
    id: int
    name: str


@pytest.mark.asyncio
async def test_async_database_connect_and_close():
    db = async_database.Database(TEST_DB_URL)
    conn = await db.connect()
    assert conn is not None
    await conn.close()
    await db.close()


@pytest.mark.asyncio
async def test_async_database_transaction_and_pydantic():
    db = async_database.Database(TEST_DB_URL)
    async with db.transaction() as conn:
        result = await conn.query("SELECT 1 as id, 'Test' as name")
        row = await conn.fetch_one("SELECT 1 as id, 'Test' as name", User)
        assert isinstance(row, User)
        assert row.id == 1
        assert row.name == "Test"
    await db.close()
