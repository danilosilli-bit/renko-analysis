import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.mt5_realtime_client import MT5RealtimeClient
from market.realtime_tick import RealtimeTick
from services.market_service import MarketService


SYMBOL = "Bra50"


def print_tick(tick: RealtimeTick) -> None:
    print(
        f"{tick.timestamp_ms} | "
        f"price={tick.price:.0f} | "
        f"bid={tick.bid:.0f} | "
        f"ask={tick.ask:.0f} | "
        f"spread={tick.spread:.0f} | "
        f"source={tick.source_price}"
    )


def main():
    client = MT5RealtimeClient()

    print("Conectando ao MT5...")
    client.connect()

    market_service = MarketService(
        mt5_client=client,
        symbol=SYMBOL,
    )

    market_service.subscribe(print_tick)

    print(f"Iniciando MarketService para {SYMBOL}...")
    market_service.start()

    try:
        time.sleep(20)

    finally:
        market_service.stop()
        client.disconnect()

    print()
    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)

    print(
        f"Ticks novos recebidos: "
        f"{market_service.received_ticks}"
    )

    latest = market_service.get_latest_tick()

    if latest:
        print(f"Último timestamp: {latest.timestamp_ms}")
        print(f"Último preço:     {latest.price}")
        print(f"Último bid:       {latest.bid}")
        print(f"Último ask:       {latest.ask}")
        print(f"Último spread:    {latest.spread}")


if __name__ == "__main__":
    main()