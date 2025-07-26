import os
import pytest
from typing import Optional
from pydantic import Field

from records2 import Database, BaseRecord

TEST_DB_URL = os.environ.get("TEST_DB_URL", "sqlite+aiosqlite:///:memory:")


class User(BaseRecord):
    """User model for database testing."""
    id: Optional[int] = Field(None, description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")


@pytest.mark.asyncio
async def test_database_connect_and_close():
    """Test database connection and closing."""
    db = Database(TEST_DB_URL)
    
    # Test connection
    conn = await db.connect()
    assert conn is not None
    await conn.close()
    
    # Test database close
    await db.close()


@pytest.mark.asyncio
async def test_database_transaction():
    """Test database transactions."""
    db = Database(TEST_DB_URL)
    
    try:
        async with db.transaction() as conn:
            result = await conn.query("SELECT 1 as value")
            row = result.fetchone()
            assert row[0] == 1
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_database_query_operations():
    """Test basic database query operations."""
    db = Database(TEST_DB_URL)
    
    try:
        # Create table
        conn = await db.connect()
        try:
            await conn.query("""
                CREATE TABLE IF NOT EXISTS test_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            """)
            await conn._conn.commit()
        finally:
            await conn.close()
        
        # Test fetch_all with model
        conn = await db.connect()
        try:
            # Insert test data
            await conn.query("""
                INSERT INTO test_users (name, email) 
                VALUES (:name, :email)
            """, name="Test User", email="test@example.com")
            await conn._conn.commit()
            
            # Fetch with model
            users = await conn.fetch_all("SELECT * FROM test_users", model=User)
            assert len(users) >= 1
            assert users[0].name == "Test User"
            assert users[0].email == "test@example.com"
            
            # Test fetch_one
            user = await conn.fetch_one("SELECT * FROM test_users WHERE id = :id", model=User, id=1)
            assert user is not None
            assert user.name == "Test User"
            
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_database_transaction_rollback():
    """Test transaction rollback on error."""
    db = Database(TEST_DB_URL)
    
    try:
        # Setup table
        conn = await db.connect()
        try:
            await conn.query("""
                CREATE TABLE IF NOT EXISTS test_rollback (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            await conn._conn.commit()
        finally:
            await conn.close()
        
        # Test rollback
        with pytest.raises(Exception):
            async with db.transaction() as conn:
                await conn.query("INSERT INTO test_rollback (name) VALUES (:name)", name="test1")
                # This should cause a constraint violation and rollback
                await conn.query("INSERT INTO test_rollback (name) VALUES (:name)", name="test1")
        
        # Verify rollback worked - no data should be inserted
        conn = await db.connect()
        try:
            result = await conn.query("SELECT COUNT(*) FROM test_rollback")
            count = result.fetchone()[0]
            assert count == 0
        finally:
            await conn.close()
            
    finally:
        await db.close()
