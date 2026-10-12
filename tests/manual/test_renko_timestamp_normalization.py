from datetime import datetime, timezone

from renko.renko_engine import RenkoEngine
from services.renko_service import InMemoryRenkoRepository


def main():

    engine = RenkoEngine(
        symbol="WINV26",
        brick_size=10,
        renko_repository=InMemoryRenkoRepository(),
        persist_state_every_tick=False,
    )

    values = [
        1789220000000,

        "2026-09-12T13:33:20+00:00",

        datetime(
            2026,
            9,
            12,
            13,
            33,
            20,
            tzinfo=timezone.utc,
        ),
    ]

    print()
    print("NORMALIZAÇÃO DE TEMPO")
    print("========================")

    results = []

    for value in values:

        result = engine._to_timestamp_ms(
            value
        )

        results.append(result)

        print(
            f"{repr(value):45} -> {result}"
        )

    print()
    print("RESULTADOS IGUAIS")
    print("========================")

    print(
        len(set(results)) == 1
    )


if __name__ == "__main__":
    main()