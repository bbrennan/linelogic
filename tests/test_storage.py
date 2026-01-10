"""
Storage layer tests.
"""

import sqlite3

from linelogic.storage.sqlite import get_connection, init_db


def test_init_db_creates_tables(tmp_path):
    db_path = tmp_path / "linelogic.db"
    init_db(str(db_path))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = {
        row[0]
        for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    }

    expected = {
        "recommendations",
        "odds_snapshots",
        "results",
        "model_versions",
    }

    assert expected.issubset(tables)

    conn.close()


def test_get_connection_returns_sqlite_connection(tmp_path):
    db_path = tmp_path / "linelogic.db"
    init_db(str(db_path))

    conn = get_connection(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)
    finally:
        conn.close()
