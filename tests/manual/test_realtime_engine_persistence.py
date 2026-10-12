from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from storage.sqlite_manager import SQLiteManager
from storage.renko_repository import RenkoRepository
from storage.intraday_repository import IntradayRepository
from storage.realtime_renko_repository import (
    RealtimeRenkoRepository,
)
from storage.intraday_storage import (
    reset_intraday_storage,
)

from renko.renko_engine import RenkoEngine

from market.intraday_tick import IntradayTick

from services.intraday_renko_adapter import (
    intraday_to_renko_tick,
)


HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"

BRICK_SIZE = 10


def main():

    print()
    print("RESET INTRADAY")
    print("==============================")

    reset_intraday_storage()

    historical_db = SQLiteManager(
        str(HISTORICAL_RENKO_DB)
    )

    historical_repository = RenkoRepository(
        historical_db
    )

    intraday = IntradayRepository()

    intraday.prepare_symbol(
        INTRADAY_SYMBOL
    )

    realtime_repository = RealtimeRenkoRepository(
        historical_repository=historical_repository,
        intraday_repository=intraday.renko_repository,
        historical_symbol=HISTORICAL_SYMBOL,
        intraday_symbol=INTRADAY_SYMBOL,
    )

    engine = RenkoEngine(
        symbol=HISTORICAL_SYMBOL,
        brick_size=BRICK_SIZE,
        renko_repository=realtime_repository,
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
    print("==============================")

    print(
        f"state.open  : {engine.state.open}"
    )

    print(
        f"state.last  : {engine.state.last}"
    )

    print(
        f"last close  : "
        f"{engine.last_closed_brick['close']}"
    )

    print(
        f"direction   : "
        f"{engine.last_closed_brick['direction']}"
    )

    tick = IntradayTick(
        timestamp_ms=1789221000000,

        price=188735.0,

        bid=188735.0,
        ask=188760.0,
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
        source_symbol=INTRADAY_SYMBOL,
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
    print("==============================")

    print(
        f"state.open : {engine.state.open}"
    )

    print(
        f"state.last : {engine.state.last}"
    )

    print(
        f"last close : "
        f"{engine.last_closed_brick['close']}"
    )

    print(
        f"direction  : "
        f"{engine.last_closed_brick['direction']}"
    )

    table_name = (
        intraday
        .renko_repository
        .get_table_name(
            INTRADAY_SYMBOL
        )
    )

    rows = intraday.renko_db.execute(
        f"""
        SELECT *
        FROM {table_name}
        ORDER BY id
        """
    )

    print()
    print("CACHE EM MEMÓRIA")
    print("==============================")

    print(
        f"quantidade em memória : "
        f"{len(realtime_repository.bricks)}"
    )

    for brick in realtime_repository.bricks:
        print(
            f"{brick['brick_size']}R | "
            f"{brick['open']} -> "
            f"{brick['close']} | "
            f"{brick['direction']}"
        )

    print()
    print("BRICKS INTRADAY")
    print("==============================")

    print(
        f"quantidade : {len(rows)}"
    )

    for row in rows:

        print(
            f"{row['brick_size']}R | "
            f"{row['open']} -> "
            f"{row['close']} | "
            f"{row['direction']}"
        )

    tables = intraday.renko_db.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    )

    table_names = [
        row["name"]
        for row in tables
    ]

    print()
    print("STATE INTRADAY")
    print("==============================")

    print(
        f"renko_state existe : "
        f"{'renko_state' in table_names}"
    )


if __name__ == "__main__":
    main()
    