"""
Alexandria Library - Database Connection
Supports both SQLite (local dev) and PostgreSQL (production).
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any
from urllib.parse import urlparse

from ..config import settings


# Detect database type from URL
def _is_postgres() -> bool:
    url = os.getenv("DATABASE_URL", "")
    return url.startswith("postgres://") or url.startswith("postgresql://")


class DictRow(dict):
    """Row that supports both dict and attribute access."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


if _is_postgres():
    # PostgreSQL mode
    import psycopg2
    import psycopg2.extras
    
    _pg_connection = None
    
    def _get_pg_connection():
        global _pg_connection
        if _pg_connection is None or _pg_connection.closed:
            url = os.getenv("DATABASE_URL")
            # Handle Render/Supabase URL format
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            _pg_connection = psycopg2.connect(url)
            _pg_connection.autocommit = False
        return _pg_connection
    
    def get_db():
        """Get the shared database connection."""
        return _get_pg_connection()
    
    def get_connection():
        """Get a new database connection."""
        return _get_pg_connection()
    
    class PostgresCursor:
        """Wrapper to make psycopg2 cursor behave like sqlite3."""
        def __init__(self, cursor):
            self._cursor = cursor
        
        def execute(self, sql, params=None):
            # Convert ? placeholders to %s for psycopg2
            sql = sql.replace("?", "%s")
            # Convert SQLite-specific syntax
            sql = sql.replace("INSERT OR IGNORE", "INSERT")
            sql = sql.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")
            if params:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)
            return self
        
        def executescript(self, sql):
            # For schema init, we handle this separately
            self._cursor.execute(sql)
            return self
        
        def fetchone(self):
            row = self._cursor.fetchone()
            if row is None:
                return None
            cols = [desc[0] for desc in self._cursor.description]
            return DictRow(zip(cols, row))
        
        def fetchall(self):
            rows = self._cursor.fetchall()
            if not rows:
                return []
            cols = [desc[0] for desc in self._cursor.description]
            return [DictRow(zip(cols, row)) for row in rows]
        
        @property
        def rowcount(self):
            return self._cursor.rowcount
    
    class PostgresConnection:
        """Wrapper to make psycopg2 connection behave like sqlite3."""
        def __init__(self, conn):
            self._conn = conn
        
        def execute(self, sql, params=None):
            cursor = self._conn.cursor()
            wrapper = PostgresCursor(cursor)
            return wrapper.execute(sql, params)
        
        def executescript(self, sql):
            cursor = self._conn.cursor()
            cursor.execute(sql)
            return cursor
        
        def commit(self):
            self._conn.commit()
        
        def rollback(self):
            self._conn.rollback()
        
        def close(self):
            pass  # Keep connection alive for reuse
    
    def get_db():
        """Get the shared database connection wrapper."""
        return PostgresConnection(_get_pg_connection())
    
    def init_db():
        """Initialize PostgreSQL database with schema."""
        schema_path = Path(__file__).parent / "schema_postgres.sql"
        
        if not schema_path.exists():
            # Fall back to SQLite schema and convert
            schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        conn = _get_pg_connection()
        cursor = conn.cursor()
        
        with open(schema_path, "r") as f:
            schema = f.read()
            # Skip SQLite-specific commands for Postgres
            if "PRAGMA" in schema:
                lines = [l for l in schema.split('\n') if not l.strip().startswith('PRAGMA')]
                schema = '\n'.join(lines)
            cursor.execute(schema)
        
        # Create anonymous test user
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, display_name, role)
            VALUES ('anon_test_user', 'anon@test.local', '', 'Anonymous', 'user')
            ON CONFLICT (id) DO NOTHING
        """)
        
        conn.commit()

else:
    # SQLite mode (default for local development)
    _connection: sqlite3.Connection = None
    
    def get_connection() -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(str(settings.DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def get_db() -> sqlite3.Connection:
        """Get the shared database connection."""
        global _connection
        if _connection is None:
            _connection = get_connection()
        return _connection
    
    def init_db():
        """Initialize the database with schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        conn = get_db()
        with open(schema_path, "r") as f:
            conn.executescript(f.read())
        
        # Create anonymous test user for development/testing
        conn.execute("""
            INSERT OR IGNORE INTO users (id, email, password_hash, display_name, role)
            VALUES ('anon_test_user', 'anon@test.local', '', 'Anonymous', 'user')
        """)
        
        conn.commit()


@contextmanager
def get_db_session() -> Generator[Any, None, None]:
    """Context manager for database sessions with automatic commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if not _is_postgres():
            conn.close()
