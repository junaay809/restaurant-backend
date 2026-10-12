import sqlite3
import json

database_path = "db.sqlite3"
output_path = "sqlite_export.json"

connection = sqlite3.connect(database_path)
connection.row_factory = sqlite3.Row

tables = connection.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

data = {}

for row in tables:
    table = row["name"]
    escaped_table = table.replace('"', '""')

    records = connection.execute(
        f'SELECT * FROM "{escaped_table}"'
    ).fetchall()

    data[table] = [dict(record) for record in records]

connection.close()

with open(output_path, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2, ensure_ascii=False, default=str)

print(f"SUCCESS: Exported {len(data)} tables to {output_path}")