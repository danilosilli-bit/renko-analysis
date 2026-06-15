import sqlite3 as sql
from contextlib import contextmanager

class SQLiteManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    @contextmanager
    def connect(self):
        self.conn = sql.connect(
            self.db_path,
            timeout=30,
            detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES,
        )
        self.conn.row_factory = sql.Row
        try:
            yield self.conn
            self.commit()
        except Exception:
            self.rollback()
            raise
        finally:
            self.disconnect()

    def commit(self):
        if self.conn:
            self.conn.commit()

    def rollback(self):
        if self.conn:
            self.conn.rollback()

    def execute(self, query: str, params=None):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if query.lstrip().upper().startswith("SELECT"):
                return cursor.fetchall()
            return cursor.lastrowid

    def executemany(self, query: str, seq_of_params):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, seq_of_params)
            return cursor.rowcount

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

            

