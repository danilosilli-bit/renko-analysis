from storage.intraday_repository import (
    IntradayRepository,
)


WIN_SYMBOL = "WINV26"
CFD_SYMBOL = "Bra50Oct26"

BRICK_SIZES = (10, 30, 45)


FIELDS_TO_COMPARE = (
    "brick_size",
    "open_time",
    "close_time",
    "open",
    "close",
    "high",
    "low",
    "direction",
)


def main():

    intraday_repository = (
        IntradayRepository()
    )

    renko_repository = (
        intraday_repository.renko_repository
    )

    print()
    print("VALIDAÇÃO WIN x CFD")
    print("=" * 60)

    all_ok = True

    for brick_size in BRICK_SIZES:

        win_brick = (
            renko_repository
            .get_last_closed_brick(
                WIN_SYMBOL,
                brick_size,
            )
        )

        cfd_brick = (
            renko_repository
            .get_last_closed_brick(
                CFD_SYMBOL,
                brick_size,
            )
        )

        print()
        print(f"{brick_size}R")
        print("-" * 60)

        if win_brick is None:

            print(
                f"ERRO: nenhum brick encontrado "
                f"para {WIN_SYMBOL}"
            )

            all_ok = False
            continue

        if cfd_brick is None:

            print(
                f"ERRO: nenhum brick encontrado "
                f"para {CFD_SYMBOL}"
            )

            all_ok = False
            continue

        brick_ok = True

        for field in FIELDS_TO_COMPARE:

            win_value = win_brick[field]
            cfd_value = cfd_brick[field]

            equal = (
                win_value == cfd_value
            )

            status = (
                "OK"
                if equal
                else "DIFERENTE"
            )

            print(
                f"{field:12} | "
                f"WIN={win_value} | "
                f"CFD={cfd_value} | "
                f"{status}"
            )

            if not equal:
                brick_ok = False
                all_ok = False

        if brick_ok:

            print()
            print(
                f"{brick_size}R: "
                f"ÚLTIMO BRICK IDÊNTICO"
            )

    print()
    print("=" * 60)

    if all_ok:

        print(
            "RESULTADO: TODAS AS TRILHAS "
            "ESTÃO IDÊNTICAS"
        )

    else:

        raise AssertionError(
            "Existem diferenças entre "
            "as trilhas WIN e CFD."
        )


if __name__ == "__main__":
    main()