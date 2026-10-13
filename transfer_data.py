import os
import sqlite3
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.db import connections, transaction
from menu.models import Category, MenuItem, DiscoveryTag

SOURCE_DB = Path(__file__).resolve().parent / "db.sqlite3"

if not SOURCE_DB.exists():
    raise FileNotFoundError(f"SQLite database not found: {SOURCE_DB}")

if connections["default"].vendor != "postgresql":
    raise RuntimeError("STOP: Destination is not PostgreSQL.")

source = sqlite3.connect(SOURCE_DB)
source.row_factory = sqlite3.Row

def get_rows(table):
    return source.execute(f'SELECT * FROM "{table}"').fetchall()

def get_columns(table):
    return {
        column["name"]
        for column in source.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()
    }

category_table = "menu_category"
item_table = "menu_menuitem"

category_rows = get_rows(category_table)
item_rows = get_rows(item_table)

print(f"Source categories: {len(category_rows)}")
print(f"Source menu items: {len(item_rows)}")

print("\nSTOP: No records have been imported.")
print("The source data and destination model schemas must be mapped")
print("before importing to avoid corrupting existing records.")

source.close()