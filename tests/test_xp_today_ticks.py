from datetime import datetime, time, timezone

import MetaTrader5 as mt5


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

SYMBOL = "WINV26"


def main():

    if not mt5.initialize(
        path=XP_MT5_PATH
    ):
        raise RuntimeError(
            f"Falha MT5: {mt5.last_error()}"
        )

    try:

        now = datetime.now(
            timezone.utc
        )

        start = datetime.combine(
            now.date(),
            time.min,
            tzinfo=timezone.utc,
        )

        print(
            "Buscando ticks:"
        )

        print(
            "de :",
            start
        )

        print(
            "até:",
            now
        )

        ticks = mt5.copy_ticks_range(
            SYMBOL,
            start,
            now,
            mt5.COPY_TICKS_ALL,
        )

        if ticks is None:

            print(
                "Erro:",
                mt5.last_error()
            )

            return

        print()
        print("=" * 50)
        print("RESULTADO")
        print("=" * 50)

        print(
            "Quantidade:",
            len(ticks)
        )

        if len(ticks) == 0:
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
            "bid:",
            first["bid"]
        )

        print(
            "ask:",
            first["ask"]
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
            "bid:",
            last["bid"]
        )

        print(
            "ask:",
            last["ask"]
        )

        print(
            "last:",
            last["last"]
        )

    finally:

        mt5.shutdown()


if __name__ == "__main__":
    main()