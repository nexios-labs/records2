import asyncio

from records import Database, Record


class Repo(Record):
    name: str
    url: str
    language: str
    stars: int


db = Database("sqlite+aiosqlite:///example_records.db")


async def main():
    conn = await db.connect()
    try:
        await conn.query(
            "CREATE TABLE IF NOT EXISTS repos (name TEXT, url TEXT, language TEXT, stars INTEGER)"
        )
        await conn.bulk_query(
            "INSERT INTO repos (name, url, language, stars) VALUES (:name, :url, :language, :stars)",
            [
                {
                    "name": "records",
                    "url": "https://github.com/kennethreitz/records",
                    "language": "Python",
                    "stars": 100,
                },
                {
                    "name": "nexios",
                    "url": "https://github.com/dunamix/nexios",
                    "language": "Python",
                    "stars": 42,
                },
            ],
        )
        repos = await conn.fetch_all("SELECT * FROM repos", model=Repo)
        for repo in repos:
            print(repo)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
