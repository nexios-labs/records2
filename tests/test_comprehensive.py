"""
Comprehensive test suite for Records2 library.

Tests all major functionality:
- Async database operations
- Pydantic model integration
- Transaction management
- Error handling
- Connection management
"""

import pytest
from typing import Optional
from pydantic import Field, ValidationError
from datetime import datetime

from records2 import Database, BaseRecord


class User(BaseRecord):
    """User model for comprehensive testing."""
    id: Optional[int] = Field(None, description="User ID")
    name: str = Field(..., min_length=1, max_length=100, description="User name")
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$', description="Email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    is_active: bool = Field(True, description="Whether user is active")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class Product(BaseRecord):
    """Product model for testing relationships."""
    id: Optional[int] = Field(None, description="Product ID")
    name: str = Field(..., min_length=1, description="Product name")
    price: float = Field(..., gt=0, description="Product price")
    category: str = Field(..., description="Product category")


@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete Records2 workflow from setup to cleanup."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # 1. Setup database schema
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # 2. Insert data with Pydantic validation
        test_users = [
            {"name": "Alice Johnson", "email": "alice@example.com", "age": 28, "is_active": True},
            {"name": "Bob Smith", "email": "bob@example.com", "age": 35, "is_active": True},
            {"name": "Charlie Brown", "email": "charlie@example.com", "age": 22, "is_active": False},
        ]
        
        async with db.transaction() as conn:
            for user_data in test_users:
                # Validate with Pydantic before inserting
                user = User(**user_data)
                await conn.query("""
                    INSERT INTO users (name, email, age, is_active)
                    VALUES (:name, :email, :age, :is_active)
                """, **user.model_dump(exclude={'id', 'created_at'}))
        
        # 3. Query with automatic Pydantic validation
        conn = await db.connect()
        try:
            # Fetch all users
            users = await conn.fetch_all("SELECT * FROM users ORDER BY id", model=User)
            assert len(users) == 3
            assert all(isinstance(user, User) for user in users)
            assert users[0].name == "Alice Johnson"
            assert users[0].email == "alice@example.com"
            
            # Fetch single user
            user = await conn.fetch_one("SELECT * FROM users WHERE email = :email", 
                                      model=User, email="bob@example.com")
            assert user is not None
            assert user.name == "Bob Smith"
            assert user.age == 35
            
            # Test Pydantic model features
            user_dict = user.model_dump()
            assert "name" in user_dict
            assert "email" in user_dict
            
            user_json = user.model_dump_json()
            assert '"name":"Bob Smith"' in user_json
            
        finally:
            await conn.close()
        
        # 4. Test aggregations and complex queries
        conn = await db.connect()
        try:
            # Count active users
            result = await conn.query("SELECT COUNT(*) FROM users WHERE is_active = :active", active=True)
            active_count = result.fetchone()[0]
            assert active_count == 2
            
            # Average age
            result = await conn.query("SELECT AVG(age) FROM users")
            avg_age = result.fetchone()[0]
            assert avg_age == (28 + 35 + 22) / 3
            
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_pydantic_validation_comprehensive():
    """Test comprehensive Pydantic validation scenarios."""
    
    # Valid user creation
    user = User(
        name="John Doe",
        email="john.doe@example.com",
        age=30,
        is_active=True,
        created_at=datetime.now()
    )
    assert user.name == "John Doe"
    assert user.age == 30
    
    # Test field validation - name too short
    with pytest.raises(ValidationError) as exc_info:
        User(name="", email="john@example.com", age=30)
    assert "String should have at least 1 character" in str(exc_info.value)
    
    # Test field validation - invalid email
    with pytest.raises(ValidationError) as exc_info:
        User(name="John", email="invalid-email", age=30)
    assert "String should match pattern" in str(exc_info.value)
    
    # Test field validation - age too high
    with pytest.raises(ValidationError) as exc_info:
        User(name="John", email="john@example.com", age=200)
    assert "Input should be less than or equal to 150" in str(exc_info.value)
    
    # Test optional fields
    minimal_user = User(name="Jane", email="jane@example.com")
    assert minimal_user.age is None
    assert minimal_user.is_active is True  # Default value
    assert minimal_user.created_at is None


@pytest.mark.asyncio
async def test_transaction_rollback():
    """Test transaction rollback on errors."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Setup table
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL
                )
            """)
        
        # Insert initial data
        async with db.transaction() as conn:
            await conn.query("INSERT INTO users (name, email) VALUES (:name, :email)",
                           name="Alice", email="alice@example.com")
        
        # Test rollback on constraint violation
        with pytest.raises(Exception):  # Should rollback
            async with db.transaction() as conn:
                await conn.query("INSERT INTO users (name, email) VALUES (:name, :email)",
                               name="Bob", email="bob@example.com")
                # This should cause a constraint violation and rollback
                await conn.query("INSERT INTO users (name, email) VALUES (:name, :email)",
                               name="Charlie", email="alice@example.com")  # Duplicate email
        
        # Verify rollback - Bob should not be in database
        conn = await db.connect()
        try:
            result = await conn.query("SELECT COUNT(*) FROM users")
            count = result.fetchone()[0]
            assert count == 1  # Only Alice should remain
            
            users = await conn.fetch_all("SELECT * FROM users", model=User)
            assert len(users) == 1
            assert users[0].name == "Alice"
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_connection_management():
    """Test proper connection management and cleanup."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Test manual connection management
        conn = await db.connect()
        assert conn is not None
        
        # Test query execution
        result = await conn.query("SELECT 1 as test_value")
        row = result.fetchone()
        assert row[0] == 1
        
        # Test connection close
        await conn.close()
        
        # Test transaction context manager
        async with db.transaction() as conn:
            result = await conn.query("SELECT 2 as test_value")
            row = result.fetchone()
            assert row[0] == 2
        # Connection should be automatically closed
        
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_multiple_models():
    """Test working with multiple Pydantic models."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Setup tables for both models
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            """)
            
            await conn.query("""
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT NOT NULL
                )
            """)
        
        # Insert data for both models
        async with db.transaction() as conn:
            # Insert user
            user = User(name="Alice", email="alice@example.com")
            await conn.query("""
                INSERT INTO users (name, email) VALUES (:name, :email)
            """, **user.model_dump(exclude={'id', 'age', 'is_active', 'created_at'}))
            
            # Insert product
            product = Product(name="Laptop", price=999.99, category="Electronics")
            await conn.query("""
                INSERT INTO products (name, price, category) VALUES (:name, :price, :category)
            """, **product.model_dump(exclude={'id'}))
        
        # Query both models
        conn = await db.connect()
        try:
            users = await conn.fetch_all("SELECT * FROM users", model=User)
            products = await conn.fetch_all("SELECT * FROM products", model=Product)
            
            assert len(users) == 1
            assert len(products) == 1
            assert isinstance(users[0], User)
            assert isinstance(products[0], Product)
            assert users[0].name == "Alice"
            assert products[0].name == "Laptop"
            assert products[0].price == 999.99
            
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_error_handling():
    """Test comprehensive error handling."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Test SQL syntax error
        conn = await db.connect()
        try:
            with pytest.raises(Exception):  # Should raise SQL syntax error
                await conn.query("INVALID SQL SYNTAX")
        finally:
            await conn.close()
        
        # Test table not exists error
        conn = await db.connect()
        try:
            with pytest.raises(Exception):  # Should raise table not found error
                await conn.fetch_all("SELECT * FROM nonexistent_table", model=User)
        finally:
            await conn.close()
        
        # Test Pydantic validation in fetch
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE invalid_users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    age TEXT  -- Wrong type for age
                )
            """)
            
            # Insert invalid data
            await conn.query("""
                INSERT INTO invalid_users (name, email, age) 
                VALUES ('John', 'john@example.com', 'not_a_number')
            """)
        
        # This should raise validation error when trying to create User model
        conn = await db.connect()
        try:
            with pytest.raises(Exception):  # Pydantic validation error
                await conn.fetch_all("SELECT * FROM invalid_users", model=User)
        finally:
            await conn.close()
            
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_performance_and_bulk_operations():
    """Test performance with bulk operations."""
    db = Database("sqlite+aiosqlite:///:memory:")
    
    try:
        # Setup table
        async with db.transaction() as conn:
            await conn.query("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    age INTEGER
                )
            """)
        
        # Bulk insert
        async with db.transaction() as conn:
            for i in range(100):
                user = User(name=f"User{i}", email=f"user{i}@example.com", age=20 + (i % 50))
                await conn.query("""
                    INSERT INTO users (name, email, age) VALUES (:name, :email, :age)
                """, **user.model_dump(exclude={'id', 'is_active', 'created_at'}))
        
        # Bulk query
        conn = await db.connect()
        try:
            users = await conn.fetch_all("SELECT * FROM users ORDER BY id", model=User)
            assert len(users) == 100
            
            # Test filtering
            young_users = await conn.fetch_all(
                "SELECT * FROM users WHERE age < :max_age ORDER BY id", 
                model=User, max_age=30
            )
            assert len(young_users) > 0
            assert all(user.age < 30 for user in young_users if user.age is not None)
            
        finally:
            await conn.close()
            
    finally:
        await db.close()
