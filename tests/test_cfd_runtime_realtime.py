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


ACTIVTRADES_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 - ActivTrades\terminal64.exe"
)

CFD_SYMBOL = "Bra50Oct26"

RENKO_SYMBOL = "WINV26"

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
    print("TESTE CFD RUNTIME REALTIME")
    print("=" * 60)

    # ========================================================
    # ACTIVTRADES
    # ========================================================

    mt5_client = MT5RealtimeClient(
        path=ACTIVTRADES_MT5_PATH,
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
        # TICK INICIAL DO CFD
        # ====================================================

        raw_tick = mt5_client.get_tick(
            CFD_SYMBOL
        )

        bid = float(
            raw_tick["bid"]
        )

        ask = float(
            raw_tick["ask"]
        )

        last = float(
            raw_tick["last"]
        )

        print()
        print("TICK INICIAL")
        print("=" * 60)

        print(
            "bid    :",
            bid,
        )

        print(
            "ask    :",
            ask,
        )

        print(
            "last   :",
            last,
        )

        print(
            "spread :",
            ask - bid,
        )

        if bid <= 0:

            raise RuntimeError(
                "BID do CFD inválido: "
                f"{bid}"
            )

        # ====================================================
        # CFD RUNTIME
        #
        # O Renko continua usando configuração do WIN.
        #
        # Neste teste o estado inicial é artificial.
        # Queremos validar somente:
        #
        # ActivTrades
        #     ↓
        # Bra50Oct26
        #     ↓
        # RealtimeTick
        #     ↓
        # BID
        #     ↓
        # RenkoService
        # ====================================================

        cfd_runtime = RenkoService(
            symbol=RENKO_SYMBOL,
            brick_sizes=BRICK_SIZES,
        )

        cfd_runtime.initialize(
            initial_price=bid,
        )

        # ====================================================
        # INICIALIZA ESTADO DOS ENGINES
        # ====================================================

        dummy_tick = {
            "timestamp_ms": int(
                raw_tick["time_msc"]
            ),
            "last": bid,
            "volume": 0.0,
            "buy_qty": 0.0,
            "sell_qty": 0.0,
            "buy_financial": 0.0,
            "sell_financial": 0.0,
        }

        for brick_size in BRICK_SIZES:

            cfd_runtime.engines[
                brick_size
            ]._initialize_state(
                dummy_tick
            )

        # ====================================================
        # GUARDA ESTADO ANTES DO REALTIME
        # ====================================================

        before = {}

        for brick_size in BRICK_SIZES:

            before[
                brick_size
            ] = state_values(
                cfd_runtime.engines[
                    brick_size
                ].state
            )

        # ====================================================
        # CALLBACK CFD
        #
        # Não reconstruímos IntradayTick aqui.
        #
        # O MarketService já entrega RealtimeTick.
        #
        # O RenkoService.process_tick() já possui o adapter
        # necessário para transformar esse RealtimeTick
        # no formato usado pelo RenkoEngine.
        # ====================================================

        received_prices = []

        def process_cfd_tick(
            realtime_tick,
        ):

            received_prices.append(
                {
                    "timestamp_ms":
                        realtime_tick.timestamp_ms,

                    "price":
                        realtime_tick.price,

                    "bid":
                        realtime_tick.bid,

                    "ask":
                        realtime_tick.ask,

                    "last":
                        realtime_tick.last,

                    "spread":
                        realtime_tick.spread,

                    "source_price":
                        realtime_tick.source_price,
                }
            )

            cfd_runtime.process_tick(
                realtime_tick
            )

        # ====================================================
        # MARKET SERVICE
        # ====================================================

        market_service = MarketService(
            mt5_client=mt5_client,
            symbol=CFD_SYMBOL,
            poll_interval=0.02,
        )

        market_service.subscribe(
            process_cfd_tick
        )

        print()
        print(
            f"Monitorando CFD por "
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
        # RESULTADO DO FEED
        # ====================================================

        print()
        print("RESULTADO DO FEED")
        print("=" * 60)

        print(
            "ticks recebidos :",
            market_service.received_ticks,
        )

        print(
            "ticks válidos   :",
            len(received_prices),
        )

        if received_prices:

            first_tick = (
                received_prices[0]
            )

            last_tick = (
                received_prices[-1]
            )

            print()

            print(
                "primeiro BID          :",
                first_tick["bid"],
            )

            print(
                "primeiro ASK          :",
                first_tick["ask"],
            )

            print(
                "primeiro LAST         :",
                first_tick["last"],
            )

            print(
                "preço usado           :",
                first_tick["price"],
            )

            print(
                "fonte do preço        :",
                first_tick[
                    "source_price"
                ],
            )

            print()

            print(
                "último BID            :",
                last_tick["bid"],
            )

            print(
                "último ASK            :",
                last_tick["ask"],
            )

            print(
                "último LAST           :",
                last_tick["last"],
            )

            print(
                "último preço usado    :",
                last_tick["price"],
            )

            print(
                "última fonte do preço :",
                last_tick[
                    "source_price"
                ],
            )

        # ====================================================
        # ESTADOS RENKO
        # ====================================================

        print()
        print("ESTADOS RENKO CFD")
        print("=" * 60)

        any_changed = False

        for brick_size in BRICK_SIZES:

            after = state_values(
                cfd_runtime.engines[
                    brick_size
                ].state
            )

            changed = (
                after
                !=
                before[brick_size]
            )

            if changed:

                any_changed = True

            repository = (
                cfd_runtime.repositories[
                    brick_size
                ]
            )

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
                "bricks repo  :",
                len(
                    repository.bricks
                ),
            )

            # -----------------------------------------------
            # O primeiro brick do repository é apenas o seed
            # criado por initialize().
            # -----------------------------------------------

            closed_bricks = max(
                len(repository.bricks) - 1,
                0,
            )

            print(
                "bricks novos :",
                closed_bricks,
            )

        # ====================================================
        # VALIDAÇÃO
        # ====================================================

        print()
        print("=" * 60)

        if (
            market_service.received_ticks
            <= 0
        ):

            raise AssertionError(
                "Nenhum tick realtime "
                "foi recebido da ActivTrades."
            )

        if not received_prices:

            raise AssertionError(
                "Nenhum RealtimeTick "
                "válido foi recebido."
            )

        first_tick = (
            received_prices[0]
        )

        # ----------------------------------------------------
        # REGRA CFD:
        #
        # preço analítico = BID
        # ----------------------------------------------------

        if (
            first_tick["price"]
            !=
            first_tick["bid"]
        ):

            raise AssertionError(
                "O preço analítico do CFD "
                "não está usando BID."
            )

        if (
            first_tick["source_price"]
            !=
            "bid"
        ):

            raise AssertionError(
                "A fonte do preço CFD "
                "não foi identificada "
                "como BID."
            )

        if not any_changed:

            raise AssertionError(
                "Os ticks CFD foram recebidos, "
                "mas nenhum estado Renko mudou."
            )

        print(
            "RESULTADO: "
            "ACTIVTRADES/BID -> "
            "CFD RUNTIME OK"
        )

    finally:

        mt5_client.disconnect()


if __name__ == "__main__":
    main()