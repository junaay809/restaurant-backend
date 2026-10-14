import os
import sqlite3
import time
from pathlib import Path

import psycopg
from psycopg import sql
from dotenv import load_dotenv

# Load the public Railway connection URL from .env.
load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "db.sqlite3"
DATABASE_URL = os.environ.get("DATABASE_URL")

MAX_RETRIES = 3


def connect_postgres():
    """Open a fresh PostgreSQL connection, retrying transient failures."""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return psycopg.connect(
                DATABASE_URL,
                sslmode="require",
                connect_timeout=20,
                application_name="sqlite_to_railway_transfer",
            )
        except psycopg.Error as error:
            last_error = error
            print(f"Connection attempt {attempt}/{MAX_RETRIES} failed: {error}")

            if attempt < MAX_RETRIES:
                time.sleep(attempt * 2)

    raise last_error


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing from .env")

    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {SQLITE_PATH}")

    source = sqlite3.connect(SQLITE_PATH)
    source.row_factory = sqlite3.Row
    source.execute("PRAGMA foreign_keys = ON")

    try:
        # Read source tables and their columns.
        source_tables = [
            row["name"]
            for row in source.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                  AND name != 'django_migrations'
                ORDER BY name
            """).fetchall()
        ]

        # Read target schema information.
        with connect_postgres() as destination:
            with destination.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name, column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                """)
                column_types = {
                    (table, column): data_type
                    for table, column, data_type in cursor.fetchall()
                }

                cursor.execute("""
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.constraint_schema = kcu.constraint_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                     AND ccu.constraint_schema = tc.constraint_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = 'public'
                """)
                foreign_keys = cursor.fetchall()

                cursor.execute("""
                    SELECT
                        tc.table_name,
                        kcu.column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.constraint_schema = kcu.constraint_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                      AND tc.table_schema = 'public'
                """)
                primary_keys = {}
                for table, column in cursor.fetchall():
                    primary_keys.setdefault(table, []).append(column)

        # Only process tables that exist in both databases.
        common_tables = [
            table for table in source_tables
            if any(key[0] == table for key in column_types)
        ]

        for table in source_tables:
            if table not in common_tables:
                print(f"SKIPPED: {table} — not found in PostgreSQL")

        # Build parent-before-child ordering from foreign keys.
        dependencies = {table: set() for table in common_tables}

        for child, _column, parent, _parent_column in foreign_keys:
            if child in dependencies and parent in dependencies and child != parent:
                dependencies[child].add(parent)

        ordered_tables = []
        remaining = {table: set(parents) for table, parents in dependencies.items()}

        while remaining:
            ready = sorted(
                table for table, parents in remaining.items()
                if not parents
            )

            if not ready:
                cycle_tables = ", ".join(sorted(remaining))
                raise RuntimeError(
                    "Foreign-key dependency cycle detected among these tables: "
                    f"{cycle_tables}. No data was deleted. We must handle this "
                    "cycle explicitly before continuing."
                )

            for table in ready:
                ordered_tables.append(table)
                remaining.pop(table)

            for parents in remaining.values():
                parents.difference_update(ready)

        # Transfer each table in its own connection and transaction.
        failures = []

        for table in ordered_tables:
            records = source.execute(
                f'SELECT * FROM "{table}"'
            ).fetchall()

            if not records:
                print(f"EMPTY: {table}")
                continue

            columns = [
                row["name"]
                for row in source.execute(
                    f'PRAGMA table_info("{table}")'
                ).fetchall()
            ]

            pk_columns = primary_keys.get(table, [])

            if not pk_columns:
                failures.append(
                    (table, "No PostgreSQL primary key found; safe upsert unavailable")
                )
                print(f"FAILED: {table} — no primary key found")
                continue

            update_columns = [
                column for column in columns
                if column not in pk_columns
            ]

            insert_statement = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table),
                sql.SQL(", ").join(map(sql.Identifier, columns)),
                sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            )

            if update_columns:
                conflict_action = sql.SQL("DO UPDATE SET {}").format(
                    sql.SQL(", ").join(
                        sql.SQL("{} = EXCLUDED.{}").format(
                            sql.Identifier(column),
                            sql.Identifier(column),
                        )
                        for column in update_columns
                    )
                )
            else:
                conflict_action = sql.SQL("DO NOTHING")

            statement = sql.SQL("{} ON CONFLICT ({}) {}").format(
                insert_statement,
                sql.SQL(", ").join(map(sql.Identifier, pk_columns)),
                conflict_action,
            )

            try:
                with connect_postgres() as destination:
                    with destination.cursor() as cursor:
                        for record in records:
                            values = []

                            for column in columns:
                                value = record[column]
                                pg_type = column_types.get((table, column), "")

                                if pg_type == "boolean" and value is not None:
                                    value = bool(value)

                                values.append(value)

                            cursor.execute(statement, tuple(values))

                print(f"SUCCESS: {table} — {len(records)} records synchronized")

            except Exception as error:
                failures.append((table, str(error)))
                print(f"FAILED: {table} — {error}")

        # Reset sequences after importing explicit primary keys.
        with connect_postgres() as destination:
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

                    if not sequence:
                        continue

                    cursor.execute(
                        sql.SQL("SELECT MAX({}) FROM {}").format(
                            sql.Identifier(column),
                            sql.Identifier(table),
                        )
                    )
                    maximum = cursor.fetchone()[0]

                    if maximum is None:
                        cursor.execute(
                            "SELECT setval(%s, 1, false)",
                            (sequence,),
                        )
                    else:
                        cursor.execute(
                            "SELECT setval(%s, %s, true)",
                            (sequence, maximum),
                        )

        print("\n========== TRANSFER SUMMARY ==========")

        if failures:
            print(f"INCOMPLETE: {len(failures)} table(s) failed.")
            for table, error in failures:
                print(f"- {table}: {error}")
            raise RuntimeError(
                "Transfer was incomplete. Review the errors above before retrying."
            )

        print(f"All {len(ordered_tables)} common tables processed.")
        print(
            "NOTE: This is an upsert, not an exact mirror. PostgreSQL-only "    
            "records have not been deleted."
        )

    finally:
        source.close()


if __name__ == "__main__":
    main()