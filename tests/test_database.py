import os

import pytest

from records2 import database

TEST_DB_URL = os.environ.get("TEST_DB_URL", "sqlite:///:memory:")


def test_database_connect_and_close():
    db = database.Database(TEST_DB_URL)
    engine = db.get_engine()
    assert engine is not None
    db.close()
    assert db._engine is None


def test_database_transaction():
    db = database.Database(TEST_DB_URL)
    with db.transaction() as conn:
        result = conn.query("SELECT 1 as value", fetchall=True)
        assert result[0]["value"] == 1
    db.close()
