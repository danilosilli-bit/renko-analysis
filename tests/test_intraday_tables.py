import sqlite3

from config.storage_config import (
    INTRADAY_TICKS_DB,
    INTRADAY_RENKO_DB,
)


def list_tables(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        )

        return [
            row[0]
            for row in cursor.fetchall()
        ]


def main():
    print()
    print("TABELAS - TICKS")
    print("----------------")

    tick_tables = list_tables(
        INTRADAY_TICKS_DB
    )

    for table in tick_tables:
        print(table)

    print()
    print("TABELAS - RENKO")
    print("----------------")

    renko_tables = list_tables(
        INTRADAY_RENKO_DB
    )

    for table in renko_tables:
        print(table)


if __name__ == "__main__":
    main()