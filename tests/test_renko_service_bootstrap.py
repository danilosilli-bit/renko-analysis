from config.storage_config import HISTORICAL_RENKO_DB

from storage.sqlite_manager import SQLiteManager
from storage.renko_repository import RenkoRepository
from storage.intraday_repository import IntradayRepository
from storage.intraday_storage import reset_intraday_storage

from services.renko_service import RenkoService


HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"


def main():

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

    service = RenkoService(
        symbol=HISTORICAL_SYMBOL,
        brick_sizes=(10, 30, 45),
    )

    service.initialize_from_history(
        historical_repository=historical_repository,
        intraday_repository=intraday.renko_repository,
        historical_symbol=HISTORICAL_SYMBOL,
        intraday_symbol=INTRADAY_SYMBOL,
    )

    print()
    print("RENKO SERVICE - BOOTSTRAP")
    print("==============================")

    for brick_size in (10, 30, 45):

        state = service.get_state(
            brick_size
        )

        engine = service.engines[
            brick_size
        ]

        print()
        print(f"{brick_size}R")
        print("------------------------------")

        print(
            f"state.open      : {state.open}"
        )

        print(
            f"state.last      : {state.last}"
        )

        print(
            f"state.high      : {state.high}"
        )

        print(
            f"state.low       : {state.low}"
        )

        print(
            "last brick close: "
            f"{engine.last_closed_brick['close']}"
        )

        print(
            "last direction  : "
            f"{engine.last_closed_brick['direction']}"
        )

    from market.intraday_tick import IntradayTick

    print()
    print("PROCESSANDO TICK INTRADAY")
    print("==============================")

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

    service.process_intraday_tick(tick)

    print()
    print("BRICKS GERADOS")
    print("==============================")

    for brick_size in (10, 30, 45):

        bricks = service.repositories[
            brick_size
        ].bricks

        print(
            f"{brick_size}R : {len(bricks)}"
        )

        for brick in bricks:
            print(
                f"  {brick['open']} -> "
                f"{brick['close']} | "
                f"{brick['direction']}"
            )

if __name__ == "__main__":
    main()