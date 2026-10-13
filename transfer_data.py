import os
import sqlite3
from pathlib import Path

import django
from django.db import connections, transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from menu.models import Category, DiscoveryTag, MenuItem

# Original SQLite database
SQLITE_FILE = Path(__file__).resolve().parent / "db.sqlite3"

if not SQLITE_FILE.exists():
    raise FileNotFoundError(f"SQLite database not found: {SQLITE_FILE}")

# Confirm Railway PostgreSQL is the destination
if connections["default"].vendor != "postgresql":
    raise RuntimeError(
        "STOP: Django is not connected to PostgreSQL. "
        "No records were transferred."
    )

source = sqlite3.connect(SQLITE_FILE)
source.row_factory = sqlite3.Row

def rows(table):
    return source.execute(f'SELECT * FROM "{table}"').fetchall()

def columns(table):
    return [col["name"] for col in source.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()]

def value(row, name, default=None):
    return row[name] if name in row.keys() else default

print("Source:", SQLITE_FILE)
print("Destination: Railway PostgreSQL")
print("Source categories:", len(rows("menu_category")))
print("Source menu items:", len(rows("menu_menuitem")))

print("\nSafety check complete.")
print("No records have been changed.")
source.close()