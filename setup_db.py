"""Builds cat_cafe.db from schema.sql and data.sql.

Run this again any time you change the schema or the data:
    python setup_db.py
"""
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "cat_cafe.db"


def build():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
    conn.executescript((HERE / "data.sql").read_text(encoding="utf-8"))
    conn.commit()

    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
    print(f"Built {DB_PATH.name}:")
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<12} {count:>5} rows")
    problems = conn.execute("PRAGMA foreign_key_check").fetchall()
    if problems:
        print("WARNING: foreign key problems:", problems)
    conn.close()


if __name__ == "__main__":
    build()
