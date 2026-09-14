import time

from ingestion.mt5_realtime_client import (
    MT5RealtimeClient,
)

from services.market_service import (
    MarketService,
)

from services.renko_service import (
    RenkoService,
)


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

WIN_SYMBOL = "WINV26"

BRICK_SIZES = (
    10,
    30,
    45,
)

TEST_SECONDS = 10


def state_values(state):

    return {
        "open": state.open,
        "last": state.last,
        "high": state.high,
        "low": state.low,
        "volume": state.volume,
        "trades_count": state.trades_count,
    }


def main():

    print()
    print("TESTE WIN RUNTIME REALTIME")
    print("=" * 60)

    # ========================================================
    # MT5 XP
    # ========================================================

    mt5_client = MT5RealtimeClient(
        path=XP_MT5_PATH,
    )

    mt5_client.connect()

    try:

        account = (
            mt5_client.get_account_info()
        )

        print(
            "company :",
            account.get("company"),
        )

        print(
            "server  :",
            account.get("server"),
        )

        # ====================================================
        # PREÇO INICIAL
        # ====================================================

        raw_tick = mt5_client.get_tick(
            WIN_SYMBOL
        )

        initial_price = float(
            raw_tick["last"]
        )

        if initial_price <= 0:

            raise RuntimeError(
                "LAST do WIN inválido: "
                f"{initial_price}"
            )

        print(
            "preço inicial WIN :",
            initial_price,
        )

        # ====================================================
        # RENKO SERVICE
        #
        # Neste teste isolado não estamos fazendo bootstrap.
        # Queremos validar apenas:
        #
        # MarketService
        #       ↓
        # RealtimeTick
        #       ↓
        # RenkoService
        # ====================================================

        win_runtime = RenkoService(
            symbol=WIN_SYMBOL,
            brick_sizes=BRICK_SIZES,
        )

        win_runtime.initialize(
            initial_price=initial_price,
        )

        # Inicializa o estado dos engines.

        dummy_tick = {
            "timestamp_ms": int(
                raw_tick["time_msc"]
            ),
            "last": initial_price,
            "volume": 0.0,
            "buy_qty": 0.0,
            "sell_qty": 0.0,
            "buy_financial": 0.0,
            "sell_financial": 0.0,
        }

        for brick_size in BRICK_SIZES:

            win_runtime.engines[
                brick_size
            ]._initialize_state(
                dummy_tick
            )

        before = {}

        for brick_size in BRICK_SIZES:

            before[brick_size] = (
                state_values(
                    win_runtime.engines[
                        brick_size
                    ].state
                )
            )

        # ====================================================
        # MARKET SERVICE
        # ====================================================

        market_service = MarketService(
            mt5_client=mt5_client,
            symbol=WIN_SYMBOL,
            poll_interval=0.02,
        )

        # O RenkoService já possui process_tick()
        # para RealtimeTick.

        market_service.subscribe(
            win_runtime.process_tick
        )

        print()
        print(
            f"Monitorando WIN por "
            f"{TEST_SECONDS}s..."
        )

        market_service.start()

        try:

            time.sleep(
                TEST_SECONDS
            )

        finally:

            market_service.stop()

        # ====================================================
        # RESULTADO
        # ====================================================

        print()
        print("RESULTADO")
        print("=" * 60)

        print(
            "ticks recebidos :",
            market_service.received_ticks,
        )

        latest_tick = (
            market_service.get_latest_tick()
        )

        if latest_tick is not None:

            print(
                "último tick    :",
                latest_tick.timestamp_ms,
            )

            print(
                "último preço   :",
                latest_tick.last,
            )

        # ====================================================
        # VALIDAÇÃO
        # ====================================================

        any_changed = False

        print()
        print("ESTADOS RENKO")
        print("=" * 60)

        for brick_size in BRICK_SIZES:

            after = state_values(
                win_runtime.engines[
                    brick_size
                ].state
            )

            changed = (
                after !=
                before[brick_size]
            )

            if changed:
                any_changed = True

            print()

            print(
                f"{brick_size}R"
            )

            print("-" * 60)

            print(
                "estado mudou :",
                changed,
            )

            print(
                "before last  :",
                before[
                    brick_size
                ]["last"],
            )

            print(
                "after last   :",
                after["last"],
            )

            print(
                "high         :",
                after["high"],
            )

            print(
                "low          :",
                after["low"],
            )

            print(
                "bricks novos :",
                len(
                    win_runtime
                    .repositories[
                        brick_size
                    ]
                    .bricks
                ),
            )

        print()
        print("=" * 60)

        if (
            market_service.received_ticks
            <= 0
        ):

            raise AssertionError(
                "Nenhum tick realtime "
                "foi recebido da XP."
            )

        if not any_changed:

            raise AssertionError(
                "Os ticks foram recebidos, "
                "mas nenhum estado Renko mudou."
            )

        print(
            "RESULTADO: "
            "XP REALTIME -> WIN RUNTIME OK"
        )

    finally:

        mt5_client.disconnect()


if __name__ == "__main__":
    main()
    