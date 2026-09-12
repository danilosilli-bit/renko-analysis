from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from market.intraday_tick import IntradayTick

from services.intraday_market_pipeline import (
    IntradayMarketPipeline,
)

from services.renko_service import (
    RenkoService,
)

from storage.intraday_repository import (
    IntradayRepository,
)

from storage.intraday_storage import (
    reset_intraday_storage,
)

from storage.renko_repository import (
    RenkoRepository,
)

from storage.sqlite_manager import (
    SQLiteManager,
)


HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"


print("RESET INTRADAY")
print("=" * 30)

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


renko_service = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=[10, 30, 45],
)

renko_service.initialize_from_history(
    historical_repository=historical_repository,
    intraday_repository=intraday.renko_repository,
    historical_symbol=HISTORICAL_SYMBOL,
    intraday_symbol=INTRADAY_SYMBOL,
)


pipeline = IntradayMarketPipeline(
    tick_repository=intraday.tick_repository,
    renko_service=renko_service,
    symbol=INTRADAY_SYMBOL,
)


tick = IntradayTick(
    timestamp_ms=1789221000000,
    price=188735.0,
    bid=188735.0,
    ask=188760.0,
    last=0.0,
    spread=25.0,
    source_type="CFD",
    source_symbol=INTRADAY_SYMBOL,
    price_source="bid",
)


print()
print("PROCESSANDO TICK")
print("=" * 30)

pipeline.process_tick(
    tick
)


print()
print("TICKS SALVOS")
print("=" * 30)

tick_count = intraday.tick_repository.count_ticks(
    INTRADAY_SYMBOL
)

print(
    "quantidade :",
    tick_count,
)


print()
print("BRICKS GERADOS")
print("=" * 30)

for brick_size in [10, 30, 45]:

    repository = renko_service.repositories[
        brick_size
    ]

    print(
        f"{brick_size}R : "
        f"{len(repository.bricks)}"
    )

    for brick in repository.bricks:
        print(
            f"  "
            f"{brick['open']} "
            f"-> "
            f"{brick['close']} "
            f"| "
            f"{brick['direction']}"
        )