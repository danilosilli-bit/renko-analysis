from copy import deepcopy

from market.intraday_tick import (
    IntradayTick,
)

from services.renko_service import (
    RenkoService,
)

from storage.intraday_repository import (
    IntradayRepository,
)


WIN_SYMBOL = "WINV26"
CFD_SYMBOL = "Bra50Oct26"

BRICK_SIZES = (
    10,
    30,
    45,
)


def state_values(state):

    return {
        "open_time": state.open_time,
        "open": state.open,
        "last": state.last,
        "high": state.high,
        "low": state.low,
        "volume": state.volume,
        "trades_count": state.trades_count,
    }


def main():

    # --------------------------------
    # Serviço que representa o estado
    # final antes da bifurcação
    # --------------------------------

    bootstrap_service = RenkoService(
        symbol=WIN_SYMBOL,
        brick_sizes=BRICK_SIZES,
    )

    bootstrap_service.initialize(
        initial_price=186000,
    )

    dummy_tick = {
        "timestamp_ms": 1,
        "last": 186000.0,
        "volume": 0.0,
        "buy_qty": 0.0,
        "sell_qty": 0.0,
        "buy_financial": 0.0,
        "sell_financial": 0.0,
    }

    for brick_size in BRICK_SIZES:

        bootstrap_service.engines[
            brick_size
        ]._initialize_state(
            dummy_tick
        )

    snapshot = (
        bootstrap_service
        .get_runtime_snapshot()
    )

    # --------------------------------
    # Repository intraday
    # --------------------------------

    intraday_repository = (
        IntradayRepository()
    )

    intraday_repository.prepare_symbol(
        WIN_SYMBOL
    )

    intraday_repository.prepare_symbol(
        CFD_SYMBOL
    )

    # --------------------------------
    # Bifurcação
    # --------------------------------

    win_service = RenkoService(
        symbol=WIN_SYMBOL,
        brick_sizes=BRICK_SIZES,
    )

    cfd_service = RenkoService(
        symbol=WIN_SYMBOL,
        brick_sizes=BRICK_SIZES,
    )

    win_service.initialize_from_snapshot(
        snapshot=deepcopy(snapshot),
        intraday_repository=(
            intraday_repository
            .renko_repository
        ),
        intraday_symbol=WIN_SYMBOL,
    )

    cfd_service.initialize_from_snapshot(
        snapshot=deepcopy(snapshot),
        intraday_repository=(
            intraday_repository
            .renko_repository
        ),
        intraday_symbol=CFD_SYMBOL,
    )

    # --------------------------------
    # Guarda estado CFD antes
    # --------------------------------

    cfd_before = {}

    for brick_size in BRICK_SIZES:

        cfd_before[brick_size] = (
            state_values(
                cfd_service.engines[
                    brick_size
                ].state
            )
        )

    # --------------------------------
    # Tick SOMENTE no WIN
    #
    # Movimento pequeno para atualizar
    # estado sem necessariamente fechar
    # um brick.
    # --------------------------------

    win_tick = IntradayTick(
        timestamp_ms=2,
        price=186005.0,
        bid=186005.0,
        ask=186010.0,
        last=186005.0,
        spread=5.0,
        volume=1.0,
        volume_real=1.0,
        flags=0,
        is_auction=None,
        buy_qty=0.0,
        sell_qty=0.0,
        buy_financial=0.0,
        sell_financial=0.0,
        source_type="FUTURES",
        source_symbol=WIN_SYMBOL,
        price_source="last",
        source_transition=False,
    )

    win_service.process_intraday_tick(
        win_tick
    )

    # --------------------------------
    # Validação
    # --------------------------------

    print()
    print("TESTE DE BIFURCAÇÃO")
    print("=" * 60)

    all_ok = True

    for brick_size in BRICK_SIZES:

        win_state = state_values(
            win_service.engines[
                brick_size
            ].state
        )

        cfd_state = state_values(
            cfd_service.engines[
                brick_size
            ].state
        )

        cfd_unchanged = (
            cfd_state ==
            cfd_before[brick_size]
        )

        win_changed = (
            win_state !=
            cfd_before[brick_size]
        )

        independent_objects = (
            win_service.engines[
                brick_size
            ].state
            is not
            cfd_service.engines[
                brick_size
            ].state
        )

        print()
        print(f"{brick_size}R")
        print("-" * 60)

        print(
            "WIN mudou             :",
            win_changed,
        )

        print(
            "CFD permaneceu igual  :",
            cfd_unchanged,
        )

        print(
            "objetos independentes :",
            independent_objects,
        )

        print(
            "WIN last              :",
            win_state["last"],
        )

        print(
            "CFD last              :",
            cfd_state["last"],
        )

        if not (
            win_changed
            and cfd_unchanged
            and independent_objects
        ):
            all_ok = False

    print()
    print("=" * 60)

    if all_ok:

        print(
            "RESULTADO: BIFURCAÇÃO "
            "INDEPENDENTE VALIDADA"
        )

    else:

        raise AssertionError(
            "Falha na independência "
            "WIN x CFD."
        )


if __name__ == "__main__":
    main()