
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text

from .record import Record, RecordCollection


class Database:
    """Main interface for database operations."""

    def __init__(self, db_url=None, **kwargs):
        self.db_url = db_url
        self._engine = None
        self._connection = None
        self._kwargs = kwargs
        if not self.db_url:
            self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise Exception("No database URL provided.")

    def get_engine(self):
        if self._engine is None:
            self._engine = create_engine(self.db_url, **self._kwargs)
        return self._engine

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def __enter__(self):
        return self

    def __exit__(self, exc, val, traceback):
        self.close()

    def __repr__(self):
        return f"<Database url={self.db_url}>"

    def get_table_names(self, internal=False, **kwargs):
        engine = self.get_engine()
        inspector = inspect(engine)
        return inspector.get_table_names()

    def get_connection(self, close_with_result=False):
        engine = self.get_engine()
        conn = engine.connect()
        return Connection(conn, close_with_result=close_with_result)

    def query(self, query, fetchall=False, **params):
        with self.get_connection() as conn:
            return conn.query(query, fetchall=fetchall, **params)

    def bulk_query(self, query, *multiparams):
        with self.get_connection() as conn:
            return conn.bulk_query(query, *multiparams)

    def query_file(self, path, fetchall=False, **params):
        with open(path) as f:
            query = f.read()
        return self.query(query, fetchall=fetchall, **params)

    def bulk_query_file(self, path, *multiparams):
        with open(path) as f:
            query = f.read()
        return self.bulk_query(query, *multiparams)

    @contextmanager
    def transaction(self):
        conn = self.get_connection()
        trans = conn._connection.begin()
        try:
            yield conn
            trans.commit()
        except Exception:
            trans.rollback()
            raise
        finally:
            conn.close()


class Connection:
    def __init__(self, connection, close_with_result=False):
        self._connection = connection
        self._close_with_result = close_with_result

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc, val, traceback):
        self.close()

    def __repr__(self):
        return f"<Connection closed={self._connection is None}>"

    def query(self, query, fetchall=False, **params):
        result = self._connection.execute(text(query), params)
        if result.returns_rows:
            keys = result.keys()
            records = (Record(keys, row) for row in result)
            collection = RecordCollection(records)
            if fetchall:
                return collection.all()
            return collection
        else:
            return result

    def bulk_query(self, query, *multiparams):
        if len(multiparams) == 1 and isinstance(multiparams[0], list):
            result = self._connection.execute(text(query), multiparams[0])
        else:
            result = self._connection.execute(text(query), *multiparams)
        return result

    def query_file(self, path, fetchall=False, **params):
        with open(path) as f:
            query = f.read()
        return self.query(query, fetchall=fetchall, **params)

    def bulk_query_file(self, path, *multiparams):
        with open(path) as f:
            query = f.read()
        return self.bulk_query(query, *multiparams)

    @contextmanager
    def transaction(self):
        trans = self._connection.begin()
        try:
            yield self
            trans.commit()
        except Exception:
            trans.rollback()
            raise
