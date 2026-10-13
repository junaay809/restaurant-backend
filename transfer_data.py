import os
import sqlite3
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(override=True)

sqlite_path = Path(__file__).resolve().parent / "db.sqlite3"
source = sqlite3.connect(sqlite_path)
source.row_factory = sqlite3.Row

database_url = os.environ["DATABASE_URL"]

with psycopg.connect(database_url, sslmode="require") as destination:
    with destination.cursor() as cursor:

        # Read PostgreSQL tables and column types.
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
        """)

        column_types = {
            (table, column): data_type
            for table, column, data_type in cursor.fetchall()
        }

        tables = source.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
              AND name != 'django_migrations'
            ORDER BY name
        """).fetchall()

        table_names = [row["name"] for row in tables]

        # Transfer categories first, then menu items, then other tables.
        table_names.sort(key=lambda table: (
            0 if table == "menu_category" else
            1 if table == "menu_menuitem" else 2
        ))

        for table in table_names:
            if not any(key[0] == table for key in column_types):
                print(f"SKIPPED: {table} — not found in PostgreSQL")
                continue

            columns = [
                row["name"]
                for row in source.execute(
                    f'PRAGMA table_info("{table}")'
                ).fetchall()
            ]

            records = source.execute(
                f'SELECT * FROM "{table}"'
            ).fetchall()

            if not records:
                continue

            # Use a separate transaction for each table.
            try:
                with destination.transaction():
                    with destination.cursor() as table_cursor:
                        column_names = ", ".join(
                            f'"{column}"' for column in columns
                        )
                        placeholders = ", ".join(
                            ["%s"] * len(columns)
                        )

                        for record in records:
                            values = []

                            for column in columns:
                                value = record[column]
                                pg_type = column_types.get(
                                    (table, column), ""
                                )

                                if pg_type == "boolean" and value is not None:
                                    value = bool(value)

                                values.append(value)

                            table_cursor.execute(
                                f'INSERT INTO "{table}" '
                                f'({column_names}) VALUES ({placeholders}) '
                                f'ON CONFLICT DO NOTHING',
                                tuple(values),
                            )

                print(f"SUCCESS: {table} — {len(records)} records processed")

            except Exception as error:
                print(f"FAILED: {table} — {error}")

        # Synchronize PostgreSQL auto-increment IDs with imported IDs.
        with destination.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND column_default LIKE 'nextval(%'
            """)

            for table, column in cursor.fetchall():
                cursor.execute(
                    "SELECT pg_get_serial_sequence(%s, %s)",
                    (f"public.{table}", column),
                )
                sequence = cursor.fetchone()[0]

                if sequence:
                    cursor.execute(
                        f'SELECT MAX("{column}") FROM "{table}"'
                    )
                    maximum = cursor.fetchone()[0]

                    if maximum is not None:
                        cursor.execute(
                            "SELECT setval(%s, %s, true)",
                            (sequence, maximum),
                        )

source.close()
print("Transfer attempt finished.")