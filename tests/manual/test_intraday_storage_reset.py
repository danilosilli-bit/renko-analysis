from config.storage_config import (
    INTRADAY_TICKS_DB,
    INTRADAY_RENKO_DB,
)

from storage.intraday_repository import IntradayRepository
from storage.intraday_storage import reset_intraday_storage


SYMBOL = "Bra50Oct26"


def main():

    # ---------------------------------
    # 1. Cria uma base intraday
    # ---------------------------------

    repository = IntradayRepository()

    repository.prepare_symbol(
        SYMBOL
    )

    print()
    print("ANTES DO RESET")
    print("========================")

    print(
        "ticks.db:",
        INTRADAY_TICKS_DB.exists()
    )

    print(
        "renko.db:",
        INTRADAY_RENKO_DB.exists()
    )

    # ---------------------------------
    # 2. Descarta referências aos DBs
    # ---------------------------------

    del repository

    # ---------------------------------
    # 3. Remove a base temporária
    # ---------------------------------

    reset_intraday_storage()

    print()
    print("DEPOIS DO RESET")
    print("========================")

    print(
        "ticks.db:",
        INTRADAY_TICKS_DB.exists()
    )

    print(
        "renko.db:",
        INTRADAY_RENKO_DB.exists()
    )

    # ---------------------------------
    # 4. Cria a nova sessão
    # ---------------------------------

    repository = IntradayRepository()

    repository.prepare_symbol(
        SYMBOL
    )

    print()
    print("NOVA SESSÃO")
    print("========================")

    print(
        "ticks.db:",
        INTRADAY_TICKS_DB.exists()
    )

    print(
        "renko.db:",
        INTRADAY_RENKO_DB.exists()
    )

    print()
    print("Base intraday recriada com sucesso.")


if __name__ == "__main__":
    main()