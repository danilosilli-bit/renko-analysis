import sqlite3

from config.storage_config import (
    INTRADAY_TICKS_DB,
    INTRADAY_RENKO_DB,
)


def show_columns(db_path, table_name):
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        for row in rows:
            print(
                f"{row[1]:20} {row[2]}"
            )


def main():
    print()
    print("TICKS")
    print("========================")

    show_columns(
        INTRADAY_TICKS_DB,
        "ticks_bra50oct26"
    )

    print()
    print("RENKO")
    print("========================")

    show_columns(
        INTRADAY_RENKO_DB,
        "renko_bra50oct26"
    )


if __name__ == "__main__":
    main()