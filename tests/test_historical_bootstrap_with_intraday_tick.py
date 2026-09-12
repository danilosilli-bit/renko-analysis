from config.storage_config import HISTORICAL_RENKO_DB

from storage.sqlite_manager import SQLiteManager
from storage.renko_repository import RenkoRepository

from renko.renko_engine import RenkoEngine

from market.intraday_tick import IntradayTick

from services.intraday_renko_adapter import (
    intraday_to_renko_tick,
)


SYMBOL = "WINV26"
BRICK_SIZE = 10


def main():

    db = SQLiteManager(
        str(HISTORICAL_RENKO_DB)
    )

    repository = RenkoRepository(
        db
    )

    engine = RenkoEngine(
        symbol=SYMBOL,
        brick_size=BRICK_SIZE,
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

    print()
    print("ANTES")
    print("========================")
    print(
        f"state.open_time = {engine.state.open_time}"
    )
    print(
        f"state.open      = {engine.state.open}"
    )
    print(
        f"state.last      = {engine.state.last}"
    )
    print(
        f"state.high      = {engine.state.high}"
    )
    print(
        f"state.low       = {engine.state.low}"
    )

    print()
    print("LAST CLOSED BRICK")
    print("========================")
    print(
        engine.last_closed_brick
    )

    tick = IntradayTick(
        timestamp_ms=1789221000000,

        price=188725.0,

        bid=188725.0,
        ask=188750.0,
        last=0.0,
        spread=25.0,

        volume=None,
        volume_real=None,
        flags=None,
        is_auction=None,

        buy_qty=None,
        sell_qty=None,

        buy_financial=None,
        sell_financial=None,

        source_type="CFD",
        source_symbol="Bra50Oct26",
        price_source="bid",
    )

    renko_tick = intraday_to_renko_tick(
        tick
    )

    engine.process_tick(
        renko_tick
    )

    print()
    print("DEPOIS")
    print("========================")
    print(
        f"state.open_time = {engine.state.open_time}"
    )
    print(
        f"state.open      = {engine.state.open}"
    )
    print(
        f"state.last      = {engine.state.last}"
    )
    print(
        f"state.high      = {engine.state.high}"
    )
    print(
        f"state.low       = {engine.state.low}"
    )

    print()
    print("ÚLTIMO BRICK")
    print("========================")
    print(
        engine.last_closed_brick
    )


if __name__ == "__main__":
    main()
    