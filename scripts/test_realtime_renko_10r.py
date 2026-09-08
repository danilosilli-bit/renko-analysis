import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.mt5_realtime_client import MT5RealtimeClient
from market.realtime_tick import RealtimeTick
from renko.renko_engine import RenkoEngine
from services.market_service import MarketService
from services.renko_tick_adapter import realtime_to_renko_tick


SYMBOL = "Bra50"
BRICK_SIZE = 10


class InMemoryRenkoRepository:
    """
    Repositório temporário apenas para testar
    o RenkoEngine em tempo real.

    Não grava nada no SQLite.
    """

    def __init__(self):
        self.bricks = []
        self.states = {}

    def save_brick(self, symbol, brick):
        self.bricks.append(brick.copy())

    def save_state(self, state):
        key = (state.symbol, state.brick_size)

        self.states[key] = {
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
        return self.states.get(
            (symbol, brick_size)
        )

    def get_last_closed_brick(
        self,
        symbol,
        brick_size,
    ):
        matching = [
            brick
            for brick in self.bricks
            if brick["brick_size"] == brick_size
        ]

        if not matching:
            return None

        return matching[-1]


def create_seed_brick(price: float) -> dict:
    """
    Cria um brick inicial apenas para dar uma referência
    de fechamento ao RenkoEngine.

    O preço é alinhado ao tick mínimo de 5 pontos.
    """

    aligned_price = round(price / 5) * 5

    return {
        "brick_size": BRICK_SIZE,
        "open_time": 0,
        "close_time": 0,

        "open": float(aligned_price),
        "close": float(aligned_price),

        "high": float(aligned_price),
        "low": float(aligned_price),

        # Escolhemos UP apenas como direção inicial
        # para permitir o teste da lógica existente.
        "direction": "UP",

        "volume": 0,
        "buy_qty": 0.0,
        "sell_qty": 0.0,
        "buy_financial": 0.0,
        "sell_financial": 0.0,
        "trades_count": 0,
    }


def main():
    client = MT5RealtimeClient()

    print("Conectando ao MT5...")
    client.connect()

    print("Obtendo preço inicial...")

    raw_tick = client.get_tick(SYMBOL)

    initial_price = float(raw_tick["bid"])

    print(
        f"Preço BID inicial: "
        f"{initial_price:.0f}"
    )

    repository = InMemoryRenkoRepository()

    seed_brick = create_seed_brick(
        initial_price
    )

    repository.bricks.append(seed_brick)

    print()
    print(
        f"Seed Renko criado em "
        f"{seed_brick['close']:.0f}"
    )

    engine = RenkoEngine(
        symbol=SYMBOL,
        brick_size=BRICK_SIZE,
        renko_repository=repository,
        persist_state_every_tick=False,
    )

    market_service = MarketService(
        mt5_client=client,
        symbol=SYMBOL,
    )

    last_brick_count = 1

    def process_realtime_tick(
        realtime_tick: RealtimeTick,
    ):
        nonlocal last_brick_count

        renko_tick = realtime_to_renko_tick(
            realtime_tick
        )

        engine.process_tick(
            renko_tick
        )

        current_count = len(
            repository.bricks
        )

        if current_count > last_brick_count:

            new_bricks = repository.bricks[
                last_brick_count:
            ]

            for brick in new_bricks:

                print()
                print("=" * 60)
                print("NOVO BRICK FECHADO")
                print("=" * 60)

                print(
                    f"Direção:  "
                    f"{brick['direction']}"
                )

                print(
                    f"Open:     "
                    f"{brick['open']:.0f}"
                )

                print(
                    f"Close:    "
                    f"{brick['close']:.0f}"
                )

                print(
                    f"High:     "
                    f"{brick['high']:.0f}"
                )

                print(
                    f"Low:      "
                    f"{brick['low']:.0f}"
                )

                print(
                    f"Timestamp:"
                    f" {brick['close_time']}"
                )

                print("=" * 60)
                print()

            last_brick_count = current_count

    market_service.subscribe(
        process_realtime_tick
    )

    print()
    print(
        "Monitorando Renko 10R "
        "por 60 segundos..."
    )

    print(
        "Aguardando fechamento "
        "de bricks..."
    )

    try:
        market_service.start()

        time.sleep(60)

    finally:
        market_service.stop()

        engine.flush_state()

        client.disconnect()

    print()
    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)

    # Exclui o seed.
    closed_bricks = repository.bricks[1:]

    print(
        f"Ticks recebidos: "
        f"{market_service.received_ticks}"
    )

    print(
        f"Bricks fechados: "
        f"{len(closed_bricks)}"
    )

    if engine.state is not None:

        print()
        print("Estado atual:")

        print(
            f"open  = "
            f"{engine.state.open}"
        )

        print(
            f"last  = "
            f"{engine.state.last}"
        )

        print(
            f"high  = "
            f"{engine.state.high}"
        )

        print(
            f"low   = "
            f"{engine.state.low}"
        )

    print()

    if closed_bricks:

        print("Últimos bricks:")

        for brick in closed_bricks[-10:]:

            print(
                f"{brick['direction']:4} | "
                f"{brick['open']:.0f} -> "
                f"{brick['close']:.0f}"
            )

    else:

        print(
            "Nenhum brick foi "
            "fechado durante o teste."
        )


if __name__ == "__main__":
    main()