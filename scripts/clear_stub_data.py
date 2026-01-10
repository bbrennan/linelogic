#!/usr/bin/env python3
"""
Clear stub data from database before deploying real model.

Run this script once before the first real model deployment to remove
all 52% stub predictions and start fresh with the trained model.
"""

import sqlite3
from pathlib import Path


def clear_stub_data(db_path: str = ".linelogic/linelogic.db") -> None:
    """
    Delete all stub recommendations, odds, and results.

    WARNING: This is destructive. Only run before deploying real model.
    """
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        return

    print(f"Clearing stub data from {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count existing records
    cursor.execute("SELECT COUNT(*) FROM recommendations")
    rec_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM odds_snapshots")
    odds_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM results")
    results_count = cursor.fetchone()[0]

    print(
        f"Found {rec_count} recommendations, {odds_count} odds snapshots, {results_count} results"
    )

    # Confirm deletion
    response = input("Delete all records? (yes/no): ").strip().lower()

    if response != "yes":
        print("Cancelled. No data deleted.")
        conn.close()
        return

    # Delete in order (foreign key constraints)
    cursor.execute("DELETE FROM results")
    deleted_results = cursor.rowcount

    cursor.execute("DELETE FROM odds_snapshots")
    deleted_odds = cursor.rowcount

    cursor.execute("DELETE FROM recommendations")
    deleted_recs = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"✅ Deleted:")
    print(f"   - {deleted_results} results")
    print(f"   - {deleted_odds} odds snapshots")
    print(f"   - {deleted_recs} recommendations")
    print("\nDatabase cleared. Ready for real model deployment.")


if __name__ == "__main__":
    clear_stub_data()
