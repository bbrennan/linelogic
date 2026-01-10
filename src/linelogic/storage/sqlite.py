"""
SQLite storage layer for LineLogic.

Manages database initialization and schema.
"""

import sqlite3
from pathlib import Path


def init_db(db_path: str = ".linelogic/linelogic.db") -> None:
    """
    Initialize the LineLogic database with all required tables.

    Args:
        db_path: Path to SQLite database file

    Creates tables:
        - recommendations: All model recommendations
        - odds_snapshots: Odds captured at recommendation time
        - results: Game results and outcomes
        - model_versions: Track model versions and configs
    """
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table: recommendations
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            sport TEXT NOT NULL,
            game_id TEXT NOT NULL,
            market TEXT NOT NULL,
            selection TEXT NOT NULL,
            model_prob REAL NOT NULL,
            market_prob REAL NOT NULL,
            edge REAL NOT NULL,
            stake_suggested REAL NOT NULL,
            kelly_fraction REAL NOT NULL,
            bankroll_at_time REAL NOT NULL,
            notes TEXT,
            model_version TEXT NOT NULL
        )
    """
    )

    # Table: odds_snapshots
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS odds_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            line REAL NOT NULL,
            odds_american INTEGER NOT NULL,
            odds_decimal REAL NOT NULL,
            raw_payload_json TEXT,
            FOREIGN KEY (recommendation_id) REFERENCES recommendations(id)
        )
    """
    )

    # Table: results
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_id INTEGER NOT NULL,
            settled_at TEXT NOT NULL,
            outcome_win_bool INTEGER NOT NULL,
            outcome_value_numeric REAL,
            profit_loss REAL NOT NULL,
            raw_payload_json TEXT,
            FOREIGN KEY (recommendation_id) REFERENCES recommendations(id)
        )
    """
    )

    # Table: model_versions
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS model_versions (
            version TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            git_sha TEXT,
            config_json TEXT NOT NULL
        )
    """
    )

    # Create indices for common queries
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_recommendations_sport_created
        ON recommendations(sport, created_at)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_recommendations_game_id
        ON recommendations(game_id)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_results_recommendation_id
        ON results(recommendation_id)
    """
    )

    conn.commit()
    conn.close()


def get_connection(db_path: str = ".linelogic/linelogic.db") -> sqlite3.Connection:
    """
    Get a connection to the database.

    Args:
        db_path: Path to SQLite database file

    Returns:
        sqlite3.Connection instance
    """
    return sqlite3.connect(db_path)
