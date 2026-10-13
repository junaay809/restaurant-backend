import os
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from dotenv import load_dotenv

load_dotenv(override=True)

# Source: your existing SQLite database
sqlite_path = Path(__file__).resolve().parent / "db.sqlite3"
source = sqlite3.connect(sqlite_path)
source.row_factory = sqlite3.Row

# Destination: Railway PostgreSQL
database_url = os.environ.get("DATABASE_URL")

if not database_url or not database_url.startswith(("postgres://", "postgresql://")):
    raise ValueError("DATABASE_URL must contain your Railway PostgreSQL URL.")

print("SQLite source:", sqlite_path)
print("PostgreSQL destination URL detected.")

source.close()