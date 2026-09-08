import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.mt5_realtime_client import MT5RealtimeClient
from services.market_service import MarketService
from services.renko_service import RenkoService


SYMBOL = "Bra50"


def print_brick(
    brick_size: int,
    brick: dict,
) -> None:

    print(
        f"{brick_size:>2}R | "
        f"{brick['direction']:4} | "
        f"{brick['open']:.0f} -> "
        f"{brick['close']:.0f} | "
        f"H={brick['high']:.0f} | "
        f"L={brick['low']:.0f}"
    )


def main():

    client = MT5RealtimeClient()

    print("Conectando ao MT5...")
    client.connect()

    raw_tick = client.get_tick(SYMBOL)
    initial_price = float(raw_tick["bid"])

    print(
        f"BID inicial: {initial_price:.0f}"
    )

    renko_service = RenkoService(
        symbol=SYMBOL,
        brick_sizes=(10, 30, 45),
    )

    renko_service.initialize(
        initial_price=initial_price
    )

    renko_service.subscribe(
        print_brick
    )

    market_service = MarketService(
        mt5_client=client,
        symbol=SYMBOL,
    )

    # Um único MarketService alimenta
    # os três Renko.
    market_service.subscribe(
        renko_service.process_tick
    )

    print()
    print("Renko ativos: 10R / 30R / 45R")
    print("Monitorando por 120 segundos...")
    print()

    try:

        market_service.start()

        time.sleep(120)

    finally:

        market_service.stop()
        renko_service.flush()
        client.disconnect()

    print()
    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)

    print(
        f"Ticks recebidos: "
        f"{market_service.received_ticks}"
    )

    for brick_size in (10, 30, 45):

        bricks = renko_service.get_bricks(
            brick_size
        )

        print(
            f"{brick_size:>2}R: "
            f"{len(bricks)} bricks"
        )


if __name__ == "__main__":
    main()