# Records2 🚀

**The Modern Async Python Database Toolkit with Pydantic Integration**

_A complete reimagining of database interaction for modern Python applications_

---

## Why Records2?

Records2 is a **fully async**, **Pydantic-integrated** mini-ORM that makes database operations simple, type-safe, and developer-friendly. Built from the ground up for modern Python applications.

### ✨ Key Features

- 🔥 **100% Async/Await** - No sync fallbacks, fully async architecture
- 🛡️ **Type Safety** - Full Pydantic v2 integration with automatic validation
- ⚡ **Developer Friendly** - Intuitive API that just works
- 🔄 **Transaction Support** - ACID compliance with context managers
- 🎯 **Zero Configuration** - Works out of the box with any SQL database
- 📊 **Production Ready** - Connection pooling and error handling built-in

---

## Quick Start

### Installation

```bash
pip install records2 pydantic aiosqlite  # For SQLite
# or
pip install records2 pydantic asyncpg    # For PostgreSQL
```

### Your First Query

```python
import asyncio
from records2 import Database

async def main():
    # Connect to database
    db = Database("sqlite+aiosqlite:///example.db")

    # Execute a simple query
    conn = await db.connect()
    result = await conn.query("SELECT 'Hello, Records2!' as message")
    row = result.fetchone()
    print(row[0])  # Hello, Records2!

    await conn.close()
    await db.close()

asyncio.run(main())
```

---

## Pydantic Integration

Define your data models with Pydantic for automatic validation and serialization:

```python
from typing import Optional
from datetime import datetime
from pydantic import Field, EmailStr
from records2 import Database, BaseRecord

class User(BaseRecord):
    """User model with validation."""
    id: Optional[int] = Field(None, description="User ID")
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="Valid email address")
    age: Optional[int] = Field(None, ge=0, le=150)
    is_active: bool = Field(True, description="Account status")
    created_at: Optional[datetime] = Field(None)

async def user_example():
    db = Database("sqlite+aiosqlite:///users.db")

    # Setup table
    async with db.transaction() as conn:
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

    # Insert with validation
    async with db.transaction() as conn:
        user = User(
            name="Alice Johnson",
            email="alice@example.com",
            age=28
        )
        await conn.query("""
            INSERT INTO users (name, email, age, is_active)
            VALUES (:name, :email, :age, :is_active)
        """, **user.model_dump(exclude={'id', 'created_at'}))

    # Query with automatic model creation
    conn = await db.connect()
    try:
        users = await conn.fetch_all("SELECT * FROM users", model=User)
        for user in users:
            print(f"User: {user.name} ({user.email})")
            print(f"Valid: {user.model_dump()}")  # Automatic serialization
    finally:
        await conn.close()
        await db.close()
```

---

## Database Operations

### Basic Queries

```python
async def basic_queries():
    db = Database("sqlite+aiosqlite:///example.db")
    conn = await db.connect()

    try:
        # Simple query
        result = await conn.query("SELECT COUNT(*) FROM users")
        count = result.fetchone()[0]
        print(f"Total users: {count}")

        # Parameterized query (safe from SQL injection)
        result = await conn.query(
            "SELECT * FROM users WHERE age > :min_age",
            min_age=25
        )
        rows = result.fetchall()

        # Fetch with Pydantic model
        users = await conn.fetch_all(
            "SELECT * FROM users WHERE is_active = :active",
            model=User,
            active=True
        )

        # Fetch single record
        user = await conn.fetch_one(
            "SELECT * FROM users WHERE email = :email",
            model=User,
            email="alice@example.com"
        )

    finally:
        await conn.close()
        await db.close()
```

### Transactions

```python
async def transaction_example():
    db = Database("sqlite+aiosqlite:///example.db")

    # Automatic transaction management
    async with db.transaction() as conn:
        # All operations in this block are part of one transaction
        await conn.query(
            "INSERT INTO users (name, email) VALUES (:name, :email)",
            name="Bob Smith",
            email="bob@example.com"
        )

        await conn.query(
            "UPDATE users SET is_active = :active WHERE email = :email",
            active=True,
            email="bob@example.com"
        )

        # If any operation fails, entire transaction is rolled back
        # If block completes successfully, transaction is committed

    await db.close()
```

### Error Handling with Rollback

```python
async def error_handling_example():
    db = Database("sqlite+aiosqlite:///example.db")

    try:
        async with db.transaction() as conn:
            # This will succeed
            await conn.query(
                "INSERT INTO users (name, email) VALUES (:name, :email)",
                name="Charlie Brown",
                email="charlie@example.com"
            )

            # This will fail (duplicate email) and rollback entire transaction
            await conn.query(
                "INSERT INTO users (name, email) VALUES (:name, :email)",
                name="Charlie Duplicate",
                email="charlie@example.com"  # Same email - will fail
            )

    except Exception as e:
        print(f"Transaction failed and was rolled back: {e}")
        # Charlie Brown was NOT inserted due to rollback

    await db.close()
```

---

## Advanced Features

### Multiple Models

```python
class Product(BaseRecord):
    """Product model."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    category: str
    in_stock: bool = True

class Order(BaseRecord):
    """Order model."""
    id: Optional[int] = None
    user_id: int
    product_id: int
    quantity: int = Field(..., gt=0)
    total_price: float = Field(..., gt=0)
    order_date: Optional[datetime] = None

async def multi_model_example():
    db = Database("sqlite+aiosqlite:///shop.db")

    # Setup tables
    async with db.transaction() as conn:
        await conn.query("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                in_stock BOOLEAN DEFAULT TRUE
            )
        """)

        await conn.query("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Insert products
    async with db.transaction() as conn:
        products = [
            Product(name="Laptop", price=999.99, category="Electronics"),
            Product(name="Mouse", price=29.99, category="Electronics"),
            Product(name="Book", price=19.99, category="Books"),
        ]

        for product in products:
            await conn.query("""
                INSERT INTO products (name, price, category, in_stock)
                VALUES (:name, :price, :category, :in_stock)
            """, **product.model_dump(exclude={'id'}))

    # Query different models
    conn = await db.connect()
    try:
        # Get all products
        products = await conn.fetch_all("SELECT * FROM products", model=Product)
        print(f"Found {len(products)} products")

        # Get electronics only
        electronics = await conn.fetch_all(
            "SELECT * FROM products WHERE category = :category",
            model=Product,
            category="Electronics"
        )

        for product in electronics:
            print(f"- {product.name}: ${product.price}")

    finally:
        await conn.close()
        await db.close()
```

### Bulk Operations

```python
async def bulk_operations():
    db = Database("sqlite+aiosqlite:///bulk.db")

    # Setup
    async with db.transaction() as conn:
        await conn.query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                age INTEGER
            )
        """)

    # Bulk insert
    async with db.transaction() as conn:
        users_data = [
            {"name": f"User{i}", "email": f"user{i}@example.com", "age": 20 + (i % 50)}
            for i in range(1000)
        ]

        for user_data in users_data:
            # Validate with Pydantic
            user = User(**user_data)
            await conn.query("""
                INSERT INTO users (name, email, age)
                VALUES (:name, :email, :age)
            """, **user.model_dump(exclude={'id', 'is_active', 'created_at'}))

    # Bulk query
    conn = await db.connect()
    try:
        # Get all users (automatically converted to User models)
        users = await conn.fetch_all("SELECT * FROM users ORDER BY id", model=User)
        print(f"Inserted and retrieved {len(users)} users")

        # Filter young users
        young_users = await conn.fetch_all(
            "SELECT * FROM users WHERE age < :max_age",
            model=User,
            max_age=30
        )
        print(f"Found {len(young_users)} young users")

    finally:
        await conn.close()
        await db.close()
```

---

## Database Support

Records2 works with any SQLAlchemy-supported database:

### SQLite (Development)

```python
db = Database("sqlite+aiosqlite:///app.db")
# or in-memory
db = Database("sqlite+aiosqlite:///:memory:")
```

### PostgreSQL (Production)

```python
db = Database("postgresql+asyncpg://user:password@localhost/dbname")
```

### MySQL

```python
db = Database("mysql+aiomysql://user:password@localhost/dbname")
```

---

## Real-World Example: Blog API

```python
from typing import List, Optional
from datetime import datetime
from pydantic import Field
from records2 import Database, BaseRecord

class Author(BaseRecord):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    bio: Optional[str] = None
    created_at: Optional[datetime] = None

class Post(BaseRecord):
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    author_id: int
    published: bool = Field(False)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BlogService:
    def __init__(self, database_url: str):
        self.db = Database(database_url)

    async def setup_database(self):
        """Initialize database schema."""
        async with self.db.transaction() as conn:
            await conn.query("""
                CREATE TABLE IF NOT EXISTS authors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    bio TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await conn.query("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    author_id INTEGER NOT NULL,
                    published BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES authors (id)
                )
            """)

    async def create_author(self, author: Author) -> Author:
        """Create a new author."""
        async with self.db.transaction() as conn:
            result = await conn.query("""
                INSERT INTO authors (name, email, bio)
                VALUES (:name, :email, :bio)
                RETURNING id
            """, **author.model_dump(exclude={'id', 'created_at'}))

            author_id = result.fetchone()[0]
            return await self.get_author(author_id)

    async def get_author(self, author_id: int) -> Optional[Author]:
        """Get author by ID."""
        conn = await self.db.connect()
        try:
            return await conn.fetch_one(
                "SELECT * FROM authors WHERE id = :id",
                model=Author,
                id=author_id
            )
        finally:
            await conn.close()

    async def create_post(self, post: Post) -> Post:
        """Create a new blog post."""
        async with self.db.transaction() as conn:
            result = await conn.query("""
                INSERT INTO posts (title, content, author_id, published)
                VALUES (:title, :content, :author_id, :published)
                RETURNING id
            """, **post.model_dump(exclude={'id', 'created_at', 'updated_at'}))

            post_id = result.fetchone()[0]
            return await self.get_post(post_id)

    async def get_post(self, post_id: int) -> Optional[Post]:
        """Get post by ID."""
        conn = await self.db.connect()
        try:
            return await conn.fetch_one(
                "SELECT * FROM posts WHERE id = :id",
                model=Post,
                id=post_id
            )
        finally:
            await conn.close()

    async def get_published_posts(self) -> List[Post]:
        """Get all published posts."""
        conn = await self.db.connect()
        try:
            return await conn.fetch_all(
                "SELECT * FROM posts WHERE published = TRUE ORDER BY created_at DESC",
                model=Post
            )
        finally:
            await conn.close()

    async def get_posts_by_author(self, author_id: int) -> List[Post]:
        """Get all posts by an author."""
        conn = await self.db.connect()
        try:
            return await conn.fetch_all(
                "SELECT * FROM posts WHERE author_id = :author_id ORDER BY created_at DESC",
                model=Post,
                author_id=author_id
            )
        finally:
            await conn.close()

    async def close(self):
        """Close database connection."""
        await self.db.close()

# Usage example
async def blog_example():
    blog = BlogService("sqlite+aiosqlite:///blog.db")

    try:
        # Setup database
        await blog.setup_database()

        # Create an author
        author = Author(
            name="Jane Doe",
            email="jane@example.com",
            bio="Tech writer and Python enthusiast"
        )
        created_author = await blog.create_author(author)
        print(f"Created author: {created_author.name} (ID: {created_author.id})")

        # Create posts
        post1 = Post(
            title="Getting Started with Records2",
            content="Records2 makes database operations simple and type-safe...",
            author_id=created_author.id,
            published=True
        )

        post2 = Post(
            title="Advanced Records2 Patterns",
            content="Learn advanced patterns for using Records2 in production...",
            author_id=created_author.id,
            published=False  # Draft
        )

        created_post1 = await blog.create_post(post1)
        created_post2 = await blog.create_post(post2)

        print(f"Created posts: {created_post1.title}, {created_post2.title}")

        # Query posts
        published_posts = await blog.get_published_posts()
        print(f"Published posts: {len(published_posts)}")

        author_posts = await blog.get_posts_by_author(created_author.id)
        print(f"Author's total posts: {len(author_posts)}")

        # Display published posts
        for post in published_posts:
            print(f"📝 {post.title}")
            print(f"   By author ID: {post.author_id}")
            print(f"   Published: {post.published}")
            print()

    finally:
        await blog.close()

# Run the example
if __name__ == "__main__":
    import asyncio
    asyncio.run(blog_example())
```

---

## Testing

Records2 includes comprehensive test coverage. Run tests with:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=records2
```

---

## Migration from Original Records

If you're migrating from the original Records library:

### Before (Original Records)

```python
import records

db = records.Database('sqlite:///example.db')
rows = db.query('SELECT * FROM users')
for row in rows:
    print(row.name)
```

### After (Records2)

```python
import asyncio
from records2 import Database, BaseRecord

class User(BaseRecord):
    id: int
    name: str

async def main():
    db = Database('sqlite+aiosqlite:///example.db')
    conn = await db.connect()
    try:
        users = await conn.fetch_all('SELECT * FROM users', model=User)
        for user in users:
            print(user.name)  # Type-safe access
    finally:
        await conn.close()
        await db.close()

asyncio.run(main())
```

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

Records2 is released under the MIT License. See [LICENSE](LICENSE) for details.

---

**Records2** - Making database operations simple, safe, and modern. 🚀
