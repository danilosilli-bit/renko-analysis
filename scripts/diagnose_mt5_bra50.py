import json
import time
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.mt5_realtime_client import MT5RealtimeClient


SYMBOL = "Bra50"


def print_json(title, data):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            default=str
        )
    )


def main():

    client = MT5RealtimeClient()

    try:

        print("Conectando ao MT5...")

        client.connect()

        print("MT5 conectado.")

        terminal = client.get_terminal_info()

        print_json(
            "TERMINAL",
            {
                "connected": terminal.get("connected"),
                "trade_allowed": terminal.get("trade_allowed"),
                "tradeapi_disabled":
                    terminal.get("tradeapi_disabled"),
                "company": terminal.get("company"),
                "name": terminal.get("name"),
                "build": terminal.get("build"),
            }
        )

        print_json(
            f"ESPECIFICAÇÕES - {SYMBOL}",
            client.get_symbol_spec(SYMBOL)
        )

        print_json(
            "TICK ATUAL",
            client.get_tick(SYMBOL)
        )

        print_json(
            "POSIÇÕES",
            client.get_positions(SYMBOL)
        )

        print()
        print("Monitorando ticks por 20 segundos...")
        print()

        last_time_msc = None

        end_time = time.time() + 20

        while time.time() < end_time:

            tick = client.get_tick(SYMBOL)

            time_msc = tick.get("time_msc")

            if time_msc != last_time_msc:

                last_time_msc = time_msc

                print(
                    f"bid={tick.get('bid')} | "
                    f"ask={tick.get('ask')} | "
                    f"last={tick.get('last')} | "
                    f"time={time_msc}"
                )

            time.sleep(0.2)

    finally:

        client.disconnect()

        print()
        print("MT5 desconectado.")


if __name__ == "__main__":
    main()