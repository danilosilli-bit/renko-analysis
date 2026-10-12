from ingestion.mt5_intraday_history_client import (
    MT5IntradayHistoryClient,
)

from services.intraday_tick_adapter import (
    mt5_history_to_intraday_tick,
)


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

SYMBOL = "WINV26"


def main():

    client = MT5IntradayHistoryClient(
        terminal_path=XP_MT5_PATH
    )

    client.connect()

    try:

        ticks = client.get_today_ticks(
            SYMBOL
        )

        print(
            "Ticks recebidos:",
            len(ticks)
        )

        if not ticks:
            return

        raw_tick = ticks[-1]

        tick = (
            mt5_history_to_intraday_tick(
                tick=raw_tick,
                symbol=SYMBOL,
                source_type="FUTURES",
                price_source="last",
            )
        )

        print()
        print("INTRADAY TICK")
        print("=" * 50)

        print(
            "timestamp_ms:",
            tick.timestamp_ms
        )

        print(
            "price:",
            tick.price
        )

        print(
            "bid:",
            tick.bid
        )

        print(
            "ask:",
            tick.ask
        )

        print(
            "last:",
            tick.last
        )

        print(
            "spread:",
            tick.spread
        )

        print(
            "volume:",
            tick.volume
        )

        print(
            "volume_real:",
            tick.volume_real
        )

        print(
            "source_type:",
            tick.source_type
        )

        print(
            "source_symbol:",
            tick.source_symbol
        )

        print(
            "price_source:",
            tick.price_source
        )

        print(
            "source_transition:",
            tick.source_transition
        )

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()