"""
Records2 - Basic Usage Examples

This example demonstrates the new fully async, Pydantic-integrated Records2 library.
"""

import asyncio
from datetime import datetime
from typing import Optional
from pydantic import Field

from records2 import Database, BaseRecord


# Define Pydantic models for your data
class User(BaseRecord):
    """User model with automatic validation and serialization."""
    
    __table_name__ = "users"  # Optional: specify table name
    
    id: Optional[int] = Field(None, description="User ID")
    name: str = Field(..., min_length=1, max_length=100, description="User name")
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$', description="Email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    is_active: bool = Field(True, description="Whether user is active")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class Post(BaseRecord):
    """Post model with relationship to User."""
    
    __table_name__ = "posts"
    
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    user_id: int = Field(..., description="Foreign key to users table")
    published: bool = Field(False, description="Whether post is published")
    created_at: Optional[datetime] = None


async def create_test_data(db: Database):
    """Create some test data for demonstration."""
    conn = await db.connect()
    try:
        # Create users table
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
        
        # Insert sample users (using INSERT OR IGNORE to avoid duplicates)
        sample_users = [
            ("Alice Johnson", "alice@example.com", 28, True),
            ("Bob Smith", "bob@example.com", 35, True),
            ("Charlie Brown", "charlie@example.com", 22, False),
            ("Diana Prince", "diana@example.com", 30, True),
        ]
        
        for name, email, age, is_active in sample_users:
            await conn.execute(text("""
                INSERT OR IGNORE INTO users (name, email, age, is_active)
                VALUES (?, ?, ?, ?)
            """), (name, email, age, is_active))
        
        await conn.commit()
        
    finally:
        await conn.close()


async def main():
    """Demonstrate Records2 capabilities."""
    
    # Create database connection (fully async)
    db = Database("sqlite+aiosqlite:///example.db")
    
    try:
        # Create test data first
        print("=== Setting up test data ===")
        await create_test_data(db)
        print("Test data created successfully!")
        
        # 1. BASIC QUERIES WITH AUTOMATIC PYDANTIC VALIDATION
        print("\n=== Basic Queries ===")
        
        # Use connection.fetch_all() method - this is the correct API
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
                # Show Pydantic model features
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
            
            # Insert with transaction
            async with db.transaction() as conn:
                await conn.execute(text("""
                    INSERT INTO users (name, email, age, is_active, created_at) 
                    VALUES (:name, :email, :age, :is_active, :created_at)
                """), user_model.model_dump())
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
            
            row = await result.fetchone()
            if row:
                print(f"Total users: {row['total_users']}")
                print(f"Average age: {row['avg_age']:.1f}")
                print(f"Active users: {row['active_users']}")
        finally:
            await conn.close()
        
        # 5. BULK OPERATIONS
        print("\n=== Bulk Operations ===")
        
        conn = await db.connect()
        try:
            # Multiple separate queries
            result1 = await conn.query("SELECT COUNT(*) FROM users WHERE is_active = :active", active=True)
            result2 = await conn.query("SELECT COUNT(*) FROM users WHERE age > :min_age", min_age=25)
            result3 = await conn.query("SELECT MAX(age) FROM users")
            
            row1 = await result1.fetchone()
            row2 = await result2.fetchone()
            row3 = await result3.fetchone()
            
            print(f"Active users: {row1['COUNT(*)']}")
            print(f"Users over 25: {row2['COUNT(*)']}")
            print(f"Max age: {row3['MAX(age)']}")
            
        finally:
            await conn.close()
        
        # 6. DEMONSTRATE PYDANTIC MODEL FEATURES
        print("\n=== Pydantic Model Features ===")
        
        conn = await db.connect()
        try:
            # Fetch user with full Pydantic model
            user = await conn.fetch_one("SELECT * FROM users WHERE id = 1", model=User)
            if user:
                print(f"User model: {user}")
                print(f"Model fields: {list(user.model_fields.keys())}")
                
                # Test model methods
                user_dict = user.model_dump(exclude_none=True)
                print(f"Exclude None: {user_dict}")
                
                user_json = user.model_dump_json(exclude_unset=True)
                print(f"JSON representation: {user_json}")
                
                # Test validation
                print(f"Model validation successful: {user.model_validate(user.model_dump())}")
        finally:
            await conn.close()
        
        print("\n=== Records2 Demo Complete! ===")
        
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always close the database connection
        await db.close()


# Example of custom model with advanced Pydantic features
class UserProfile(BaseRecord):
    """Extended user profile with advanced Pydantic features."""
    
    __table_name__ = "user_profiles"
    
    user_id: int = Field(..., description="Foreign key to users")
    bio: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, pattern=r'^https?://.+')
    location: Optional[str] = Field(None, max_length=100)
    
    # Computed field example
    @property
    def display_name(self) -> str:
        """Computed property for display purposes."""
        return f"User {self.user_id}"
    
    # Custom validator example
    @classmethod
    def validate_bio(cls, v):
        """Custom validation for bio field."""
        if v and len(v.strip()) == 0:
            raise ValueError("Bio cannot be empty if provided")
        return v


async def advanced_example():
    """Show advanced Pydantic integration features."""
    
    db = Database("sqlite+aiosqlite:///example.db")
    
    try:
        # Automatic validation and serialization
        profile_data = {
            "user_id": 1,
            "bio": "Software developer passionate about Python",
            "website": "https://example.com",
            "location": "San Francisco"
        }
        
        # Create and validate model
        profile = UserProfile(**profile_data)
        
        # Automatic JSON serialization
        json_data = profile.to_json()
        print(f"Profile JSON: {json_data}")
        
        # Automatic dict conversion
        dict_data = profile.to_dict()
        print(f"Profile dict: {dict_data}")
        
        # Access computed properties
        print(f"Display name: {profile.display_name}")
        
    finally:
        await db.close()


if __name__ == "__main__":
    # Run the basic example
    asyncio.run(main())
    
    # Run the advanced example
    # asyncio.run(advanced_example())
