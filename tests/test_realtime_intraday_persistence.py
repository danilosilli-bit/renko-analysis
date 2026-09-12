import time

from ingestion.mt5_realtime_client import MT5RealtimeClient
from services.market_service import MarketService
from services.intraday_tick_adapter import realtime_to_intraday_tick
from storage.intraday_repository import IntradayRepository


SYMBOL = "Bra50Oct26"
TEST_SECONDS = 20


def main():
    repository = IntradayRepository()

    repository.prepare_symbol(
        SYMBOL
    )

    repository.tick_repository.truncate_table(
        SYMBOL
    )

    mt5_client = MT5RealtimeClient()

    mt5_client.connect()

    market_service = MarketService(
        mt5_client=mt5_client,
        symbol=SYMBOL,
        poll_interval=0.02,
    )

    saved_ticks = 0


    def on_tick(realtime_tick):
        nonlocal saved_ticks

        intraday_tick = realtime_to_intraday_tick(
            realtime_tick,
            source_type="CFD",
        )

        repository.tick_repository.save_tick(
            SYMBOL,
            intraday_tick,
        )

        saved_ticks += 1

        print(
            f"{saved_ticks:4} | "
            f"price={intraday_tick.price:.0f} | "
            f"bid={intraday_tick.bid:.0f} | "
            f"ask={intraday_tick.ask:.0f} | "
            f"spread={intraday_tick.spread:.0f} | "
            f"source={intraday_tick.price_source}"
        )


    market_service.subscribe(
        on_tick
    )

    try:
        market_service.start()

        print()
        print(
            f"Monitorando {SYMBOL} "
            f"por {TEST_SECONDS}s..."
        )
        print()

        time.sleep(
            TEST_SECONDS
        )

    finally:
        market_service.stop()

        try:
            mt5_client.disconnect()
        except Exception:
            pass


    count = repository.tick_repository.count_ticks(
        SYMBOL
    )

    print()
    print("========================")
    print("RESULTADO")
    print("========================")
    print(
        f"Ticks recebidos pelo teste: {saved_ticks}"
    )
    print(
        f"Ticks gravados no banco:   {count}"
    )


    rows = repository.tick_repository.get_all_ticks(
        SYMBOL
    )

    if rows:
        print()
        print("ÚLTIMO TICK")
        print("========================")
        print(
            dict(rows[-1])
        )


if __name__ == "__main__":
    main()