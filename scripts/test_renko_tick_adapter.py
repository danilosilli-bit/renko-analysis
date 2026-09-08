import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.mt5_realtime_client import MT5RealtimeClient
from market.realtime_tick import RealtimeTick
from services.market_service import MarketService
from services.renko_tick_adapter import realtime_to_renko_tick


SYMBOL = "Bra50"


def process_tick(tick: RealtimeTick) -> None:
    renko_tick = realtime_to_renko_tick(tick)

    print(
        f"{renko_tick['timestamp_ms']} | "
        f"renko_last={renko_tick['last']:.0f} | "
        f"bid={renko_tick['bid']:.0f} | "
        f"ask={renko_tick['ask']:.0f} | "
        f"mt5_last={renko_tick['mt5_last']:.0f} | "
        f"source={renko_tick['price_source']}"
    )


def main():
    client = MT5RealtimeClient()

    print("Conectando ao MT5...")
    client.connect()

    market_service = MarketService(
        mt5_client=client,
        symbol=SYMBOL,
    )

    market_service.subscribe(process_tick)

    print("Testando adapter por 10 segundos...")

    try:
        market_service.start()
        time.sleep(10)

    finally:
        market_service.stop()
        client.disconnect()

    print()
    print("Teste concluído.")
    print(
        f"Ticks processados: "
        f"{market_service.received_ticks}"
    )


if __name__ == "__main__":
    main()