import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from renko.renko_engine import RenkoEngine


SYMBOL = "Bra50"
BRICK_SIZE = 10


class InMemoryRenkoRepository:

    def __init__(self):
        self.bricks = []
        self.states = {}

    def save_brick(self, symbol, brick):
        self.bricks.append(brick.copy())

    def save_state(self, state):
        self.states[(state.symbol, state.brick_size)] = {
            "symbol": state.symbol,
            "brick_size": state.brick_size,
            "open_time": state.open_time,
            "open": state.open,
            "last": state.last,
            "high": state.high,
            "low": state.low,
            "direction": state.direction,
            "volume": state.volume,
            "buy_qty": state.buy_qty,
            "sell_qty": state.sell_qty,
            "buy_financial": state.buy_financial,
            "sell_financial": state.sell_financial,
            "trades_count": state.trades_count,
        }

    def get_state(self, symbol, brick_size):
        return self.states.get((symbol, brick_size))

    def get_last_closed_brick(self, symbol, brick_size):
        matching = [
            brick
            for brick in self.bricks
            if brick["brick_size"] == brick_size
        ]
        return matching[-1] if matching else None


def make_tick(price, timestamp_ms):
    return {
        "symbol": SYMBOL,
        "timestamp_ms": timestamp_ms,
        "last": float(price),
        "bid": float(price),
        "ask": float(price + 20),
        "spread": 20.0,
        "volume": 0.0,
        "buy_qty": 0.0,
        "sell_qty": 0.0,
        "buy_financial": 0.0,
        "sell_financial": 0.0,
    }


def seed_repository(repository):
    repository.bricks.append({
        "brick_size": BRICK_SIZE,
        "open_time": 0,
        "close_time": 0,
        "open": 188000.0,
        "close": 188000.0,
        "high": 188000.0,
        "low": 188000.0,
        "direction": "UP",
        "volume": 0,
        "buy_qty": 0.0,
        "sell_qty": 0.0,
        "buy_financial": 0.0,
        "sell_financial": 0.0,
        "trades_count": 0,
    })


def main():

    repository = InMemoryRenkoRepository()
    seed_repository(repository)

    engine = RenkoEngine(
        symbol=SYMBOL,
        brick_size=BRICK_SIZE,
        renko_repository=repository,
        persist_state_every_tick=False,
    )

    # Movimentos propositalmente grandes para testar:
    # alta, continuação, reversão para baixo
    # e nova reversão para cima.
    prices = [
        188000,
        188025,
        188050,
        188100,
        188150,
        188100,
        188050,
        188000,
        187950,
        187900,
        187950,
        188000,
        188050,
        188100,
        188150,
    ]

    timestamp = 1_000_000

    previous_count = len(repository.bricks)

    print("=" * 70)
    print("TESTE DETERMINÍSTICO RENKO 10R")
    print("=" * 70)

    for price in prices:

        timestamp += 1000

        print()
        print(f"TICK -> {price}")

        tick = make_tick(
            price,
            timestamp,
        )

        engine.process_tick(tick)

        current_count = len(repository.bricks)

        if current_count > previous_count:

            new_bricks = repository.bricks[
                previous_count:
            ]

            for brick in new_bricks:

                print(
                    "   BRICK -> "
                    f"{brick['direction']:4} | "
                    f"{brick['open']:.0f} -> "
                    f"{brick['close']:.0f}"
                )

            previous_count = current_count

        else:
            print("   nenhum brick fechado")

    print()
    print("=" * 70)
    print("BRICKS FINAIS")
    print("=" * 70)

    # Não mostra o seed.
    for i, brick in enumerate(
        repository.bricks[1:],
        start=1,
    ):
        print(
            f"{i:02d} | "
            f"{brick['direction']:4} | "
            f"{brick['open']:.0f} -> "
            f"{brick['close']:.0f} | "
            f"H={brick['high']:.0f} | "
            f"L={brick['low']:.0f}"
        )

    print()
    print(
        f"Total de bricks fechados: "
        f"{len(repository.bricks) - 1}"
    )


if __name__ == "__main__":
    main()
    