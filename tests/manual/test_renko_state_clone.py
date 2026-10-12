from copy import deepcopy

from storage.sqlite_manager import (
    SQLiteManager,
)

from storage.renko_repository import (
    RenkoRepository,
)

from config.storage_config import (
    HISTORICAL_RENKO_DB,
)




SYMBOL = "WINV26"

BRICK_SIZES = (
    10,
    30,
    45,
)


def main():

    historical_db = SQLiteManager(
        str(HISTORICAL_RENKO_DB)
    )

    historical_repository = RenkoRepository(
        historical_db
    )

    print()
    print("TESTE DE CLONAGEM DO ESTADO")
    print("=" * 60)

    all_ok = True

    for brick_size in BRICK_SIZES:

        saved_state = (
            historical_repository.get_state(
                SYMBOL,
                brick_size,
            )
        )

        last_closed_brick = (
            historical_repository
            .get_last_closed_brick(
                SYMBOL,
                brick_size,
            )
        )

        if saved_state is None:

            print(
                f"{brick_size}R | "
                f"ERRO: estado não encontrado"
            )

            all_ok = False
            continue

        if last_closed_brick is None:

            print(
                f"{brick_size}R | "
                f"ERRO: último brick não encontrado"
            )

            all_ok = False
            continue

        saved_state_dict = dict(
            saved_state
        )

        last_closed_brick_dict = dict(
            last_closed_brick
        )


        win_state = deepcopy(
            saved_state_dict
        )

        cfd_state = deepcopy(
            saved_state_dict
        )

        win_last_brick = deepcopy(
            last_closed_brick_dict
        )

        cfd_last_brick = deepcopy(
            last_closed_brick_dict
        )

        # --------------------------------
        # Verifica conteúdo inicial
        # --------------------------------

        same_state = (
            win_state == cfd_state
        )

        same_brick = (
            win_last_brick ==
            cfd_last_brick
        )

        # --------------------------------
        # Verifica independência
        # --------------------------------

        original_cfd_last = (
            cfd_state["last"]
        )

        win_state["last"] = (
            float(win_state["last"]) + 5
        )

        independent_state = (
            cfd_state["last"] ==
            original_cfd_last
        )

        original_cfd_close = (
            cfd_last_brick["close"]
        )

        win_last_brick["close"] = (
            float(
                win_last_brick["close"]
            ) + 5
        )

        independent_brick = (
            cfd_last_brick["close"] ==
            original_cfd_close
        )

        ok = (
            same_state
            and same_brick
            and independent_state
            and independent_brick
        )

        print()
        print(f"{brick_size}R")
        print("-" * 60)

        print(
            f"estado inicial igual      : "
            f"{same_state}"
        )

        print(
            f"último brick inicial igual: "
            f"{same_brick}"
        )

        print(
            f"estado independente       : "
            f"{independent_state}"
        )

        print(
            f"último brick independente : "
            f"{independent_brick}"
        )

        if ok:

            print(
                f"{brick_size}R | CLONE OK"
            )

        else:

            print(
                f"{brick_size}R | FALHOU"
            )

            all_ok = False

    print()
    print("=" * 60)

    if all_ok:

        print(
            "RESULTADO: CLONAGEM "
            "INDEPENDENTE VALIDADA"
        )

    else:

        raise AssertionError(
            "Falha na clonagem dos estados."
        )


if __name__ == "__main__":
    main()