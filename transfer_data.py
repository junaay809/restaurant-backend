import os
import sqlite3
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()
close_old_connections()

from django.db import transaction, close_old_connections
from menu.models import Category, MenuItem

SOURCE_DB = Path(__file__).resolve().parent / "db.sqlite3"

source = sqlite3.connect(SOURCE_DB)
source.row_factory = sqlite3.Row

def rows(table):
    return source.execute(f'SELECT * FROM "{table}"').fetchall()

def columns(table):
    return {
        col["name"]
        for col in source.execute(f'PRAGMA table_info("{table}")')
    }

category_rows = rows("menu_category")
item_rows = rows("menu_menuitem")

print(f"Local categories: {len(category_rows)}")
print(f"Local menu items: {len(item_rows)}")

try:
    with transaction.atomic():
        category_map = {}

        for row in category_rows:
            data = dict(row)
            old_id = data["id"]

            category, _ = Category.objects.update_or_create(
                slug=data.get("slug") or "",
                defaults={
                    "name": data["name"],
                    "description": data.get("description") or "",
                    "is_active": bool(data.get("is_active", True)),
                    "display_order": data.get("display_order") or 0,
                },
            )
            category_map[old_id] = category

        item_columns = columns("menu_menuitem")
        imported = 0

        for row in item_rows:
            data = dict(row)
            category = category_map.get(data.get("category_id"))

            if category is None:
                raise ValueError(
                    f"Category missing for menu item: {data.get('name')}"
                )

            defaults = {
                "category": category,
                "name": data["name"],
                "country": data.get("country") or "",
                "rating": data.get("rating") or 0,
                "description": data.get("description") or "",
                "price": data["price"],
                "is_available": bool(data.get("is_available", True)),
                "is_featured": bool(data.get("is_featured", False)),
                "is_popular": bool(data.get("is_popular", False)),
                "is_spicy": bool(data.get("is_spicy", False)),
                "preparation_time": data.get("preparation_time") or 15,
                "display_order": data.get("display_order") or 0,
            }

            slug = data.get("slug")
            if not slug:
                from django.utils.text import slugify
                slug = slugify(data["name"])

            item, _ = MenuItem.objects.update_or_create(
                slug=slug,
                defaults=defaults,
            )

            imported += 1

        print(f"Imported/updated categories: {Category.objects.count()}")
        print(f"Imported/updated menu items: {imported}")
        print("Transfer completed.")

except Exception as exc:
    import traceback
    traceback.print_exc()
    raise

finally:
    source.close()