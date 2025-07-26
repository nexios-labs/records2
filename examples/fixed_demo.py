"""
Records2 - Fixed Demo

This demonstrates the Records2 library with the correct API calls.
"""

import asyncio
from datetime import datetime
from typing import Optional
from pydantic import Field

from records2 import Database, BaseRecord


class User(BaseRecord):
    """User model with automatic validation and serialization."""
    
    id: Optional[int] = Field(None, description="User ID")
    name: str = Field(..., min_length=1, max_length=100, description="User name")
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$', description="Email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    is_active: bool = Field(True, description="Whether user is active")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


async def create_test_data(db: Database):
    """Create some test data for demonstration."""
    conn = await db.connect()
    try:
        # Create users table - USING CORRECT API: conn.query()
        await conn.query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample users - USING CORRECT API: conn.query() with named params
        sample_users = [
            ("Alice Johnson", "alice@example.com", 28, True),
            ("Bob Smith", "bob@example.com", 35, True),
            ("Charlie Brown", "charlie@example.com", 22, False),
            ("Diana Prince", "diana@example.com", 30, True),
        ]
        
        for name, email, age, is_active in sample_users:
            await conn.query("""
                INSERT OR IGNORE INTO users (name, email, age, is_active)
                VALUES (:name, :email, :age, :is_active)
            """, name=name, email=email, age=age, is_active=is_active)
        
        await conn._conn.commit()
        
    finally:
        await conn.close()


async def main():
    """Demonstrate Records2 capabilities."""
    
    # Create database connection (fully async)
    db = Database("sqlite+aiosqlite:///fixed_demo.db")
    
    try:
        # Create test data first
        print("=== Setting up test data ===")
        await create_test_data(db)
        print("Test data created successfully!")
        
        # 1. BASIC QUERIES WITH AUTOMATIC PYDANTIC VALIDATION
        print("\n=== Basic Queries ===")
        
        conn = await db.connect()
        try:
            users = await conn.fetch_all("SELECT * FROM users LIMIT 5", model=User)
            
            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  User: {user.name} ({user.email}) - Age: {user.age}, Active: {user.is_active}")
            
            # Get single record using fetch_one
            user = await conn.fetch_one("SELECT * FROM users WHERE id = :id", model=User, id=1)
            if user:
                print(f"\nSingle user lookup: {user.name}")
                print(f"  As dict: {user.model_dump()}")
                print(f"  As JSON: {user.model_dump_json()}")
        finally:
            await conn.close()
        
        # 2. TRANSACTIONS AND VALIDATION
        print("\n=== Transactions and Validation ===")
        
        try:
            # Test Pydantic validation
            new_user_data = {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "age": 30,
                "is_active": True,
                "created_at": datetime.now()
            }
            
            # Pydantic validation happens automatically
            user_model = User(**new_user_data)
            print(f"Valid user created: {user_model.name}")
            
            # Insert with transaction - USING CORRECT API
            async with db.transaction() as conn:
                await conn.query("""
                    INSERT INTO users (name, email, age, is_active, created_at) 
                    VALUES (:name, :email, :age, :is_active, :created_at)
                """, **user_model.model_dump())
                print("User inserted successfully in transaction!")
                
        except Exception as e:
            print(f"Error during user creation: {e}")
        
        # 3. VALIDATION ERROR DEMONSTRATION
        print("\n=== Validation Error Demo ===")
        
        try:
            # This should fail validation
            invalid_user = User(
                name="",  # Too short
                email="invalid-email",  # Invalid format
                age=200,  # Too old
            )
        except Exception as e:
            print(f"Validation failed as expected: {e}")
        
        # 4. DYNAMIC QUERIES (NO PREDEFINED MODEL)
        print("\n=== Dynamic Queries ===")
        
        conn = await db.connect()
        try:
            result = await conn.query("""
                SELECT 
                    COUNT(*) as total_users,
                    AVG(age) as avg_age,
                    COUNT(CASE WHEN is_active THEN 1 END) as active_users
                FROM users
            """)
            
            row = result.fetchone()
            if row:
                print(f"Total users: {row[0]}")
                print(f"Average age: {row[1]:.1f}")
                print(f"Active users: {row[2]}")
        finally:
            await conn.close()
        
        print("\n=== Records2 Demo Complete! ===")
        print("✅ Async database operations working!")
        print("✅ Pydantic validation and serialization working!")
        print("✅ Transaction support working!")
        print("✅ Type-safe queries working!")
        
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always close the database connection
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
