"""[SMOKE-FIX-002] Tests for DB connection management."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from unittest import mock

import pytest


class TestGetDbPath:
    def test_returns_default_path_when_no_env(self):
        from src.backend.db.connection import get_db_path

        with mock.patch.dict(os.environ, {}, clear=True):
            path = get_db_path()

        assert path == str(Path("data/db/dev.sqlite3"))

    def test_respects_database_url_env(self):
        from src.backend.db.connection import get_db_path

        with mock.patch.dict(os.environ, {"DATABASE_URL": "sqlite:///custom/path/test.sqlite3"}, clear=True):
            path = get_db_path()

        assert path == str(Path("custom/path/test.sqlite3"))


class TestCreateConnection:
    def test_returns_sqlite3_connection(self, tmp_path):
        from src.backend.db.connection import create_connection

        db_path = str(tmp_path / "test.sqlite3")
        conn = create_connection(db_path)

        assert isinstance(conn, sqlite3.Connection)

    def test_sets_row_factory_to_row(self, tmp_path):
        from src.backend.db.connection import create_connection

        db_path = str(tmp_path / "test.sqlite3")
        conn = create_connection(db_path)

        assert conn.row_factory is sqlite3.Row

    def test_creates_parent_directory(self, tmp_path):
        from src.backend.db.connection import create_connection

        db_path = str(tmp_path / "subdir" / "test.sqlite3")
        conn = create_connection(db_path)

        assert Path(db_path).parent.exists()
        assert Path(db_path).exists()

    def test_can_execute_queries(self, tmp_path):
        from src.backend.db.connection import create_connection

        db_path = str(tmp_path / "test.sqlite3")
        conn = create_connection(db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO test (name) VALUES (?)", ["hello"])
        conn.commit()

        row = conn.execute("SELECT * FROM test WHERE name = ?", ["hello"]).fetchone()
        assert row["id"] == 1
        assert row["name"] == "hello"


class TestLifespanWiring:
    def test_app_state_has_db_connection_after_startup(self):
        """Verify FastAPI app has db_connection in app.state after lifespan startup."""
        import asyncio

        from fastapi import FastAPI

        from src.backend.api.main import lifespan

        app = FastAPI()
        app.state.db_connection = None

        async def run_lifespan():
            async with lifespan(app):
                assert hasattr(app.state, "db_connection")
                assert app.state.db_connection is not None
                assert isinstance(app.state.db_connection, sqlite3.Connection)

        asyncio.run(run_lifespan())
