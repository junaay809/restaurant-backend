import os
import sqlite3
import django

from pathlib import Path
from django.conf import settings
from django.db import connections, transaction

# Locate the original SQLite database
SQLITE_FILE = Path(__file__).resolve().parent / "db.sqlite3"

if not SQLITE_FILE.exists():
    raise FileNotFoundError(f"SQLite database not found: {SQLITE_FILE}")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

source = sqlite3.connect(SQLITE_FILE)
source.row_factory = sqlite3.Row

target = connections["default"]

if target.vendor != "postgresql":
    raise RuntimeError("STOP: Django is not connected to PostgreSQL.")

print("Source:", SQLITE_FILE)
print("Destination: Railway PostgreSQL")

# Show the source menu counts before making any changes
with source:
    categories = source.execute(
        "SELECT COUNT(*) FROM menu_category"
    ).fetchone()[0]
    items = source.execute(
        "SELECT COUNT(*) FROM menu_menuitem"
    ).fetchone()[0]

print(f"Source categories: {categories}")
print(f"Source menu items: {items}")

print("\nConnection confirmed. No records have been changed.")
print("We must map and validate the Django models before importing.")
source.close()