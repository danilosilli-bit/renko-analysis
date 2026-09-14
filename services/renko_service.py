from copy import deepcopy

from collections.abc import Callable

from market.realtime_tick import RealtimeTick
from market.instrument_config import InstrumentConfig
from market.intraday_tick import IntradayTick
from renko.renko_engine import RenkoEngine
from services.renko_tick_adapter import realtime_to_renko_tick

from storage.realtime_renko_repository import (
    RealtimeRenkoRepository,
)

from services.intraday_renko_adapter import (
    intraday_to_renko_tick,
)

BrickCallback = Callable[[int, dict], None]


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


class RenkoService:
    """
    Recebe RealtimeTick do MarketService e alimenta
    vários RenkoEngine usando o mesmo fluxo de mercado.

    Nesta etapa utiliza somente memória.
    """

    def __init__(
        self,
        symbol: str,
        brick_sizes=(10, 30, 45),
    ):
        self.symbol = symbol
        self.brick_sizes = tuple(brick_sizes)

        self.instrument = InstrumentConfig.from_symbol(symbol)

        self.repositories = {}
        self.engines = {}

        self._brick_counts = {}
        self._subscribers: list[BrickCallback] = []

    def initialize(self, initial_price: float) -> None:

        for brick_size in self.brick_sizes:

            repository = InMemoryRenkoRepository()

            seed = self._create_seed_brick(
                price=initial_price,
                brick_size=brick_size,
            )

            repository.bricks.append(seed)

            engine = RenkoEngine(
                symbol=self.symbol,
                brick_size=brick_size,
                renko_repository=repository,
                persist_state_every_tick=False,
            )

            self.repositories[brick_size] = repository
            self.engines[brick_size] = engine

            # 1 = seed
            self._brick_counts[brick_size] = 1

    def initialize_from_history(
        self,
        historical_repository,
        intraday_repository,
        historical_symbol: str,
        intraday_symbol: str,
        defer_persistence: bool = False,
    ) -> None:

        for brick_size in self.brick_sizes:

            repository = RealtimeRenkoRepository(
                historical_repository=historical_repository,
                intraday_repository=intraday_repository,
                historical_symbol=historical_symbol,
                intraday_symbol=intraday_symbol,
                defer_persistence=defer_persistence,
            )

            engine = RenkoEngine(
                symbol=historical_symbol,
                brick_size=brick_size,
                renko_repository=repository,
                persist_state_every_tick=False,
            )

            dummy_tick = {
                "timestamp_ms": 0,
                "last": 0.0,
                "volume": 0.0,
                "buy_qty": 0.0,
                "sell_qty": 0.0,
                "buy_financial": 0.0,
                "sell_financial": 0.0,
            }

            engine._initialize_state(
                dummy_tick
            )

            self.repositories[
                brick_size
            ] = repository

            self.engines[
                brick_size
            ] = engine

            self._brick_counts[
                brick_size
            ] = 0

    def subscribe(self, callback: BrickCallback) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: BrickCallback) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def process_tick(self, tick: RealtimeTick) -> None:

        renko_tick = realtime_to_renko_tick(tick)

        for brick_size in self.brick_sizes:

            engine = self.engines[brick_size]
            repository = self.repositories[brick_size]

            previous_count = self._brick_counts[brick_size]

            engine.process_tick(renko_tick)

            current_count = len(repository.bricks)

            if current_count <= previous_count:
                continue

            new_bricks = repository.bricks[
                previous_count:
            ]

            self._brick_counts[brick_size] = current_count

            for brick in new_bricks:
                self._notify(
                    brick_size,
                    brick,
                )

    def process_intraday_tick(
        self,
        tick: IntradayTick,
    ):
        renko_tick = intraday_to_renko_tick(
            tick
        )

        for brick_size in self.brick_sizes:

            engine = self.engines.get(
                brick_size
            )

            repository = self.repositories.get(
                brick_size
            )

            if engine is None or repository is None:
                continue

            bricks_before = len(
                repository.bricks
            )

            repository.set_source_transition(
                tick.source_transition
            )

            try:
                engine.process_tick(
                    renko_tick
                )
            finally:
                repository.set_source_transition(
                    False
                )

            bricks_after = len(
                repository.bricks
            )

            if bricks_after <= bricks_before:
                continue

            new_bricks = repository.bricks[
                bricks_before:bricks_after
            ]


            for brick in new_bricks:
                self._notify(
                    brick_size,
                    brick,
                )

    def get_latest_brick(
        self,
        brick_size: int,
    ) -> dict | None:

        repository = self.repositories.get(brick_size)

        if repository is None:
            return None

        # Desconsidera seed.
        if len(repository.bricks) <= 1:
            return None

        return repository.bricks[-1]

    def get_bricks(
        self,
        brick_size: int,
    ) -> list[dict]:

        repository = self.repositories.get(brick_size)

        if repository is None:
            return []

        # Não devolve seed.
        return repository.bricks[1:].copy()

    def get_state(self, brick_size: int):
        engine = self.engines.get(brick_size)

        if engine is None:
            return None

        return engine.state

    def get_runtime_snapshot(self) -> dict:

        snapshot = {}

        for brick_size in self.brick_sizes:

            engine = self.engines.get(
                brick_size
            )

            if engine is None:
                continue

            snapshot[brick_size] = {
                "state": deepcopy(
                    engine.state
                ),
                "last_closed_brick": deepcopy(
                    engine.last_closed_brick
                ),
            }

        return snapshot

    def initialize_from_snapshot(
        self,
        snapshot: dict,
        intraday_repository,
        intraday_symbol: str,
    ) -> None:

        for brick_size in self.brick_sizes:

            snapshot_data = snapshot.get(
                brick_size
            )

            if snapshot_data is None:
                raise ValueError(
                    f"Snapshot não encontrado "
                    f"para {brick_size}R"
                )

            repository = (
                RealtimeRenkoRepository(
                    historical_repository=None,
                    intraday_repository=intraday_repository,
                    historical_symbol=self.symbol,
                    intraday_symbol=intraday_symbol,
                    defer_persistence=False,
                )
            )

            engine = RenkoEngine(
                symbol=self.symbol,
                brick_size=brick_size,
                renko_repository=repository,
                persist_state_every_tick=False,
            )

            engine.state = deepcopy(
                snapshot_data["state"]
            )

            engine.last_closed_brick = deepcopy(
                snapshot_data[
                    "last_closed_brick"
                ]
            )

            self.repositories[
                brick_size
            ] = repository

            self.engines[
                brick_size
            ] = engine

            self._brick_counts[
                brick_size
            ] = 0

    def flush(self) -> None:
        for engine in self.engines.values():
            engine.flush_state()

    def _notify(
        self,
        brick_size: int,
        brick: dict,
    ) -> None:

        for callback in self._subscribers.copy():
            try:
                callback(
                    brick_size,
                    brick,
                )
            except Exception as exc:
                print(
                    "[RenkoService] erro no subscriber "
                    f"{callback}: {exc}"
                )

    def _create_seed_brick(
        self,
        price: float,
        brick_size: int,
    ) -> dict:

        aligned_price = self.instrument.round_price(price)

        return {
            "brick_size": brick_size,

            "open_time": 0,
            "close_time": 0,

            "open": float(aligned_price),
            "close": float(aligned_price),

            "high": float(aligned_price),
            "low": float(aligned_price),

            # Temporário.
            "direction": "UP",

            "volume": 0,
            "buy_qty": 0.0,
            "sell_qty": 0.0,
            "buy_financial": 0.0,
            "sell_financial": 0.0,
            "trades_count": 0,
        }