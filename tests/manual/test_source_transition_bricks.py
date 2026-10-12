from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from market.intraday_tick import IntradayTick

from services.renko_service import (
    RenkoService,
)

from storage.intraday_repository import (
    IntradayRepository,
)

from storage.intraday_storage import (
    reset_intraday_storage,
)

from storage.renko_repository import (
    RenkoRepository,
)

from storage.sqlite_manager import (
    SQLiteManager,
)


HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"

BRICK_SIZES = (10, 30, 45)


def print_bricks(
    renko_service,
    brick_size,
):
    repository = renko_service.repositories[
        brick_size
    ]

    print("")
    print(f"{brick_size}R")
    print("=" * 50)

    if not repository.bricks:
        print("Nenhum brick gerado.")
        return

    for brick in repository.bricks:

        print(
            f"{brick['open']} "
            f"-> {brick['close']} "
            f"| {brick['direction']} "
            f"| source_transition="
            f"{brick.get('source_transition')}"
        )


def main():

    # --------------------------------------------------------
    # 1. Reset intraday
    # --------------------------------------------------------

    print("")
    print("RESET INTRADAY")
    print("=" * 50)

    reset_intraday_storage()


    # --------------------------------------------------------
    # 2. Histórico Renko
    # --------------------------------------------------------

    historical_db = SQLiteManager(
        str(HISTORICAL_RENKO_DB)
    )

    historical_repository = RenkoRepository(
        historical_db
    )


    # --------------------------------------------------------
    # 3. Intraday
    # --------------------------------------------------------

    intraday_repository = IntradayRepository()

    intraday_repository.prepare_symbol(
        INTRADAY_SYMBOL
    )


    # --------------------------------------------------------
    # 4. RenkoService
    # --------------------------------------------------------

    renko_service = RenkoService(
        symbol=HISTORICAL_SYMBOL,
        brick_sizes=BRICK_SIZES,
    )

    renko_service.initialize_from_history(
        historical_repository=
            historical_repository,

        intraday_repository=
            intraday_repository.renko_repository,

        historical_symbol=
            HISTORICAL_SYMBOL,

        intraday_symbol=
            INTRADAY_SYMBOL,
    )


    # --------------------------------------------------------
    # 5. Estado inicial
    # --------------------------------------------------------

    print("")
    print("ESTADO INICIAL")
    print("=" * 50)

    for brick_size in BRICK_SIZES:

        state = renko_service.get_state(
            brick_size
        )

        print(
            f"{brick_size}R "
            f"| open={state.open} "
            f"| last={state.last} "
            f"| high={state.high} "
            f"| low={state.low}"
        )


    # --------------------------------------------------------
    # 6. Tick de transição
    #
    # Escolhemos um preço suficientemente alto para
    # provocar fechamento de bricks.
    # --------------------------------------------------------

    transition_tick = IntradayTick(
        timestamp_ms=1789169200000,
        price=189500.0,

        bid=189500.0,
        ask=189540.0,
        last=0.0,
        spread=40.0,

        volume=None,
        volume_real=None,

        flags=None,
        is_auction=None,

        buy_qty=None,
        sell_qty=None,

        buy_financial=None,
        sell_financial=None,

        source_type="CFD",
        source_symbol=INTRADAY_SYMBOL,
        price_source="bid",

        source_transition=True,
    )


    print("")
    print("PROCESSANDO TICK DE TRANSIÇÃO")
    print("=" * 50)

    print(
        f"price={transition_tick.price}"
    )

    print(
        "source_transition="
        f"{transition_tick.source_transition}"
    )

    renko_service.process_intraday_tick(
        transition_tick
    )


    # --------------------------------------------------------
    # 7. Bricks gerados pelo tick de transição
    # --------------------------------------------------------

    print("")
    print("BRICKS APÓS TRANSIÇÃO")
    print("=" * 50)

    for brick_size in BRICK_SIZES:
        print_bricks(
            renko_service,
            brick_size,
        )


    # --------------------------------------------------------
    # 8. Valida automaticamente
    # --------------------------------------------------------

    transition_brick_count = 0

    for brick_size in BRICK_SIZES:

        repository = (
            renko_service.repositories[
                brick_size
            ]
        )

        for brick in repository.bricks:

            assert (
                brick.get(
                    "source_transition"
                )
                is True
            ), (
                f"Brick {brick_size}R "
                "deveria estar marcado "
                "como source_transition=True"
            )

            transition_brick_count += 1


    assert (
        transition_brick_count > 0
    ), (
        "O tick de transição não gerou "
        "nenhum brick."
    )


    # --------------------------------------------------------
    # 9. Guarda quantidade antes do tick normal
    # --------------------------------------------------------

    counts_before_normal = {
        brick_size: len(
            renko_service.repositories[
                brick_size
            ].bricks
        )
        for brick_size in BRICK_SIZES
    }


    # --------------------------------------------------------
    # 10. Tick normal
    #
    # Preço ainda mais alto para gerar novos bricks.
    # --------------------------------------------------------

    normal_tick = IntradayTick(
        timestamp_ms=1789169260000,
        price=190500.0,

        bid=190500.0,
        ask=190540.0,
        last=0.0,
        spread=40.0,

        volume=None,
        volume_real=None,

        flags=None,
        is_auction=None,

        buy_qty=None,
        sell_qty=None,

        buy_financial=None,
        sell_financial=None,

        source_type="CFD",
        source_symbol=INTRADAY_SYMBOL,
        price_source="bid",

        source_transition=False,
    )


    print("")
    print("PROCESSANDO TICK NORMAL")
    print("=" * 50)

    print(
        f"price={normal_tick.price}"
    )

    print(
        "source_transition="
        f"{normal_tick.source_transition}"
    )

    renko_service.process_intraday_tick(
        normal_tick
    )


    # --------------------------------------------------------
    # 11. Valida apenas os novos bricks
    # --------------------------------------------------------

    normal_brick_count = 0

    print("")
    print("NOVOS BRICKS DO TICK NORMAL")
    print("=" * 50)

    for brick_size in BRICK_SIZES:

        repository = (
            renko_service.repositories[
                brick_size
            ]
        )

        start_index = (
            counts_before_normal[
                brick_size
            ]
        )

        new_bricks = repository.bricks[
            start_index:
        ]

        print("")
        print(f"{brick_size}R")
        print("-" * 50)

        if not new_bricks:
            print(
                "Nenhum novo brick."
            )

        for brick in new_bricks:

            print(
                f"{brick['open']} "
                f"-> {brick['close']} "
                f"| {brick['direction']} "
                f"| source_transition="
                f"{brick.get('source_transition')}"
            )

            assert (
                brick.get(
                    "source_transition"
                )
                is False
            ), (
                f"Brick {brick_size}R "
                "do tick normal não deveria "
                "ser source_transition=True"
            )

            normal_brick_count += 1


    assert (
        normal_brick_count > 0
    ), (
        "O tick normal não gerou "
        "nenhum novo brick."
    )


    # --------------------------------------------------------
    # 12. Resultado
    # --------------------------------------------------------

    print("")
    print("RESULTADO")
    print("=" * 50)

    print(
        f"bricks de transição : "
        f"{transition_brick_count}"
    )

    print(
        f"bricks normais      : "
        f"{normal_brick_count}"
    )

    print("")
    print(
        "TESTE SOURCE TRANSITION OK"
    )


if __name__ == "__main__":
    main()