import os
import sqlite3
from pathlib import Path
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connections, transaction
from menu.models import Category, MenuItem, DiscoveryTag

source_path = Path(__file__).resolve().parent / "db.sqlite3"

source = sqlite3.connect(source_path)
source.row_factory = sqlite3.Row

try:
    with transaction.atomic(using="default"):
        # Check the existing destination data first.
        print("Railway database connected.")
        print("Existing categories:", Category.objects.count())
        print("Existing menu items:", MenuItem.objects.count())
        print("Existing discovery tags:", DiscoveryTag.objects.count())

    print("\nNo records have been changed.")
    print("We have confirmed the connection. The next step is to map")
    print("the SQLite records to your Django models safely.")

finally:
    source.close()