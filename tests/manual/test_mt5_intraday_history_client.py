from ingestion.mt5_intraday_history_client import (
    MT5IntradayHistoryClient,
)


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

SYMBOL = "WINV26"


def main():

    client = MT5IntradayHistoryClient(
        terminal_path=XP_MT5_PATH
    )

    print(
        "Conectando ao MT5 XP..."
    )

    client.connect()

    try:

        ticks = client.get_today_ticks(
            SYMBOL
        )

        print()
        print("=" * 50)
        print("RESULTADO")
        print("=" * 50)

        print(
            "Ticks válidos:",
            len(ticks)
        )

        if not ticks:
            return

        first = ticks[0]
        last = ticks[-1]

        print()
        print("PRIMEIRO")
        print("-" * 50)

        print(
            "time_msc:",
            first["time_msc"]
        )

        print(
            "last:",
            first["last"]
        )

        print()
        print("ÚLTIMO")
        print("-" * 50)

        print(
            "time_msc:",
            last["time_msc"]
        )

        print(
            "last:",
            last["last"]
        )

    finally:

        client.disconnect()

        print()
        print(
            "MT5 XP desconectado."
        )


if __name__ == "__main__":
    main()