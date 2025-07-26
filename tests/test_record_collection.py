import pytest
from typing import Optional, List
from pydantic import Field

from records2 import Database, BaseRecord

# Test async database collection operations


class TestUser(BaseRecord):
    """Test user model for collection tests."""
    id: Optional[int] = Field(None, description="User ID")
    name: str = Field(..., min_length=1, description="User name")
    email: str = Field(..., description="Email address")


@pytest.mark.asyncio
async def test_fetch_all_collection():
    """Test fetching multiple records as a collection."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Setup table and data
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            """)
            
            # Insert test data
            for i in range(3):
                await conn.query("""
                    INSERT INTO users (name, email) 
                    VALUES (:name, :email)
                """, name=f"User{i}", email=f"user{i}@example.com")
        
        # Test fetch_all returns list of models
        conn = await db.connect()
        try:
            users = await conn.fetch_all("SELECT * FROM users ORDER BY id", model=TestUser)
            
            # Test collection properties
            assert len(users) == 3
            assert isinstance(users, list)
            assert all(isinstance(user, TestUser) for user in users)
            
            # Test iteration
            for i, user in enumerate(users):
                assert user.name == f"User{i}"
                assert user.email == f"user{i}@example.com"
            
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_fetch_all_slice_operations():
    """Test slicing operations on fetched collections."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Setup table and data
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            """)
            
            # Insert test data
            for i in range(5):
                await conn.query("""
                    INSERT INTO users (name, email) 
                    VALUES (:name, :email)
                """, name=f"User{i}", email=f"user{i}@example.com")
        
        # Test slicing
        conn = await db.connect()
        try:
            all_users = await conn.fetch_all("SELECT * FROM users ORDER BY id", model=TestUser)
            
            # Test slice operations
            first_two = all_users[:2]
            assert len(first_two) == 2
            assert first_two[0].name == "User0"
            assert first_two[1].name == "User1"
            
            # Test negative indexing
            last_user = all_users[-1]
            assert last_user.name == "User4"
            
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_fetch_one_operations():
    """Test fetch_one operations (equivalent to .first() and .one())."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Setup table and data
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            """)
            
            await conn.query("""
                INSERT INTO users (name, email) 
                VALUES (:name, :email)
            """, name="FirstUser", email="first@example.com")
        
        # Test fetch_one (equivalent to .first())
        conn = await db.connect()
        try:
            first_user = await conn.fetch_one("SELECT * FROM users ORDER BY id", model=TestUser)
            assert first_user is not None
            assert first_user.name == "FirstUser"
            
            # Test fetch_one with no results
            no_user = await conn.fetch_one("SELECT * FROM users WHERE id = 999", model=TestUser)
            assert no_user is None
            
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_collection_aggregations():
    """Test collection aggregation operations (equivalent to .scalar())."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Setup table and data
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    age INTEGER
                )
            """)
            
            # Insert test data with ages
            ages = [25, 30, 35, 40]
            for i, age in enumerate(ages):
                await conn.query("""
                    INSERT INTO users (name, email, age) 
                    VALUES (:name, :email, :age)
                """, name=f"User{i}", email=f"user{i}@example.com", age=age)
        
        # Test scalar operations
        conn = await db.connect()
        try:
            # Test COUNT
            result = await conn.query("SELECT COUNT(*) FROM users")
            count = result.fetchone()[0]
            assert count == 4
            
            # Test AVG
            result = await conn.query("SELECT AVG(age) FROM users")
            avg_age = result.fetchone()[0]
            assert avg_age == 32.5  # (25+30+35+40)/4
            
            # Test MIN/MAX
            result = await conn.query("SELECT MIN(age), MAX(age) FROM users")
            min_max = result.fetchone()
            assert min_max[0] == 25  # MIN
            assert min_max[1] == 40  # MAX
            
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_empty_collection_handling():
    """Test handling of empty collections."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Setup empty table
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            """)
        
        # Test empty collections
        conn = await db.connect()
        try:
            # Empty fetch_all
            users = await conn.fetch_all("SELECT * FROM users", model=TestUser)
            assert len(users) == 0
            assert isinstance(users, list)
            
            # Empty fetch_one
            user = await conn.fetch_one("SELECT * FROM users", model=TestUser)
            assert user is None
            
            # Empty aggregation
            result = await conn.query("SELECT COUNT(*) FROM users")
            count = result.fetchone()[0]
            assert count == 0
            
        finally:
            await conn.close()
            
    finally:
        await db.close()
