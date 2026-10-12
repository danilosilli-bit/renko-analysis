import time

from ingestion.mt5_realtime_client import (
    MT5RealtimeClient,
)

from services.market_service import (
    MarketService,
)


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

SYMBOL = "WINV26"

TEST_SECONDS = 15


def main():

    print()
    print("PROCESSO XP / WIN")
    print("=" * 50)

    client = MT5RealtimeClient(
        path=XP_MT5_PATH,
    )

    client.connect()

    try:

        account = client.get_account_info()

        print(
            "company :",
            account.get("company"),
        )

        print(
            "server  :",
            account.get("server"),
        )

        service = MarketService(
            mt5_client=client,
            symbol=SYMBOL,
            poll_interval=0.02,
        )

        service.start()

        try:

            for second in range(
                1,
                TEST_SECONDS + 1,
            ):

                time.sleep(1)

                tick = (
                    service
                    .get_latest_tick()
                )

                if tick is None:

                    print(
                        f"{second:02d}s | "
                        "aguardando tick..."
                    )

                    continue

                print(
                    f"{second:02d}s | "
                    f"ticks={service.received_ticks} | "
                    f"price={tick.price} | "
                    f"last={tick.last} | "
                    f"source={tick.source_price}"
                )

        finally:

            service.stop()

        print()
        print(
            "TOTAL TICKS XP :",
            service.received_ticks,
        )

        if (
            service.received_ticks
            <= 0
        ):

            raise AssertionError(
                "XP não recebeu ticks."
            )

        tick = (
            service
            .get_latest_tick()
        )

        if tick is None:

            raise AssertionError(
                "Último tick XP inexistente."
            )

        if (
            tick.source_price
            !=
            "last"
        ):

            raise AssertionError(
                "WIN não está usando LAST."
            )

        print(
            "RESULTADO: "
            "PROCESSO XP OK"
        )

    finally:

        client.disconnect()


if __name__ == "__main__":
    main()