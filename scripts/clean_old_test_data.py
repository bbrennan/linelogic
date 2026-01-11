#!/usr/bin/env python3
"""
Clean old stub test data from database and optionally load real predictions.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime


def get_db_path():
    """Find the database path."""
    # Check common locations
    possible_paths = [
        Path(".linelogic/linelogic.db"),
        Path(".linelogic/app.db"),
        Path("app.db"),
        Path(".streamlit/app.db"),
    ]

    for path in possible_paths:
        if path.exists():
            print(f"✅ Found database: {path}")
            return path

    print("❌ Database not found. Checked:")
    for path in possible_paths:
        print(f"   - {path}")
    return None


def clean_old_stub_data():
    """Remove old stub test data (52/50 predictions)."""
    db_path = get_db_path()
    if not db_path:
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check what's in there
        cursor.execute("SELECT COUNT(*) FROM recommendations")
        total = cursor.fetchone()[0]
        print(f"\n📊 Current data: {total} recommendations in database")

        # Delete stub data (where model_prob and market_prob are both 0.52/0.50)
        cursor.execute(
            """
            DELETE FROM recommendations 
            WHERE ROUND(model_prob, 2) = 0.52 AND ROUND(market_prob, 2) = 0.50
        """
        )

        deleted = cursor.rowcount
        conn.commit()

        # Check remaining
        cursor.execute("SELECT COUNT(*) FROM recommendations")
        remaining = cursor.fetchone()[0]

        print(f"🗑️  Deleted: {deleted} stub records")
        print(f"✅ Remaining: {remaining} records")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def show_database_structure():
    """Show what tables exist and their contents."""
    db_path = get_db_path()
    if not db_path:
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print("\n📋 Database Structure:")
        print("━" * 60)

        for (table,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:20} → {count:6} records")

        # Show schema for recommendations table if it exists
        if any(t[0] == "recommendations" for t in tables):
            print("\n📋 Recommendations Table Schema:")
            cursor.execute("PRAGMA table_info(recommendations)")
            cols = cursor.fetchall()
            for col in cols:
                print(f"  - {col[1]:25} ({col[2]})")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   CLEAN OLD STUB TEST DATA FROM DATABASE                  ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Show current state
    show_database_structure()

    # Clean old data
    print("\n" + "=" * 60)
    print("Cleaning old stub data...")
    print("=" * 60)

    if clean_old_stub_data():
        print("\n✅ Clean complete!")
        print("\n📝 Next steps:")
        print("   1. Streamlit app will auto-refresh (reload page if needed)")
        print("   2. Old 52/50 predictions will be gone")
        print("   3. Ready for tomorrow's fresh data at 9 AM UTC")
    else:
        print("\n⚠️  Could not clean database - check paths above")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
