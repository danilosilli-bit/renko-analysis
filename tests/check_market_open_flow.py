import json
import sqlite3
import urllib.request
from pathlib import Path


API_BASE = "http://127.0.0.1:8000"
INTRADAY_DB = Path("data/intraday/renko.db")

BRICK_SIZES = (10, 30, 45)
TABLE_NAME = "renko_bra50oct26"


def get_api_renko(brick_size: int) -> dict:
    url = f"{API_BASE}/api/renko/{brick_size}"

    with urllib.request.urlopen(
        url,
        timeout=10,
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def get_db_rows():
    if not INTRADAY_DB.exists():
        return []

    db = sqlite3.connect(
        INTRADAY_DB
    )

    try:
        return db.execute(
            f"""
            SELECT
                id,
                brick_size,
                open,
                close,
                direction,
                source_transition
            FROM {TABLE_NAME}
            ORDER BY id
            """
        ).fetchall()

    finally:
        db.close()


def print_api_status():
    print("")
    print("=" * 60)
    print("API")
    print("=" * 60)

    for brick_size in BRICK_SIZES:

        try:
            data = get_api_renko(
                brick_size
            )

            print("")
            print(
                f"{brick_size}R"
            )

            print(
                "initialized             :",
                data.get("initialized"),
            )

            print(
                "historical_brick_count  :",
                data.get(
                    "historical_brick_count"
                ),
            )

            print(
                "intraday_brick_count    :",
                data.get(
                    "intraday_brick_count"
                ),
            )

            print(
                "brick_count             :",
                data.get("brick_count"),
            )

            state = data.get("state")

            if state:
                print(
                    "state open             :",
                    state.get("open"),
                )

                print(
                    "state last             :",
                    state.get("last"),
                )

                print(
                    "state high             :",
                    state.get("high"),
                )

                print(
                    "state low              :",
                    state.get("low"),
                )

        except Exception as exc:

            print(
                f"{brick_size}R -> ERRO:",
                exc,
            )


def print_database_status():
    print("")
    print("=" * 60)
    print("INTRADAY DATABASE")
    print("=" * 60)

    rows = get_db_rows()

    if not rows:
        print(
            "Nenhum brick intraday "
            "persistido."
        )
        return

    transition_rows = [
        row
        for row in rows
        if row[5] == 1
    ]

    normal_rows = [
        row
        for row in rows
        if row[5] == 0
    ]

    print(
        "total bricks      :",
        len(rows),
    )

    print(
        "normal            :",
        len(normal_rows),
    )

    print(
        "source_transition :",
        len(transition_rows),
    )

    print("")
    print(
        "Primeiros/últimos registros:"
    )

    sample = (
        rows[:5] +
        rows[-5:]
    )

    for row in sample:
        print(row)

    print("")
    print("=" * 60)
    print("VALIDAÇÃO DA TRANSIÇÃO")
    print("=" * 60)

    if not transition_rows:

        print(
            "AGUARDANDO: ainda não existe "
            "brick source_transition."
        )

        print(
            "Isso pode ser normal se o "
            "primeiro tick CFD não fechou "
            "nenhum brick."
        )

        return

    first_transition_id = (
        transition_rows[0][0]
    )

    last_transition_id = (
        transition_rows[-1][0]
    )

    before_transition = [
        row
        for row in rows
        if row[0] < first_transition_id
    ]

    after_transition = [
        row
        for row in rows
        if row[0] > last_transition_id
    ]

    normal_after = [
        row
        for row in after_transition
        if row[5] == 0
    ]

    print(
        "primeiro transition id :",
        first_transition_id,
    )

    print(
        "último transition id    :",
        last_transition_id,
    )

    print(
        "bricks antes            :",
        len(before_transition),
    )

    print(
        "bricks depois           :",
        len(after_transition),
    )

    print(
        "normais depois          :",
        len(normal_after),
    )

    print("")

    print(
        "source_transition "
        "persistido: PASS"
    )

    if normal_after:
        print(
            "retorno para "
            "source_transition=0: PASS"
        )
    else:
        print(
            "retorno para "
            "source_transition=0: "
            "AGUARDANDO"
        )


def main():
    print("")
    print("=" * 60)
    print("MARKET OPEN FLOW CHECK")
    print("=" * 60)

    print_api_status()
    print_database_status()

    print("")
    print("=" * 60)
    print("FIM")
    print("=" * 60)


if __name__ == "__main__":
    main()
    