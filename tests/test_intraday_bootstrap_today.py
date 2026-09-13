from datetime import date

from config.storage_config import (
    HISTORICAL_RENKO_DB,
    HISTORICAL_TICKS_DB,
)

from storage.sqlite_manager import SQLiteManager
from storage.tick_repository import TickRepository
from storage.renko_repository import RenkoRepository
from storage.intraday_repository import IntradayRepository
from storage.intraday_storage import reset_intraday_storage

from services.renko_service import RenkoService
from services.intraday_bootstrap_service import (
    IntradayBootstrapService,
)


HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"
BRICK_SIZES = (10, 30, 45)


print()
print("RESET INTRADAY")
print("=" * 40)

reset_intraday_storage()


historical_ticks_db = SQLiteManager(
    str(HISTORICAL_TICKS_DB)
)

historical_renko_db = SQLiteManager(
    str(HISTORICAL_RENKO_DB)
)


tick_repository = TickRepository(
    historical_ticks_db
)

historical_renko_repository = RenkoRepository(
    historical_renko_db
)


intraday_repository = IntradayRepository()

intraday_repository.prepare_symbol(
    INTRADAY_SYMBOL
)


renko_service = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=BRICK_SIZES,
)


renko_service.initialize_from_history(
    historical_repository=historical_renko_repository,
    intraday_repository=intraday_repository.renko_repository,
    historical_symbol=HISTORICAL_SYMBOL,
    intraday_symbol=INTRADAY_SYMBOL,
)


print()
print("ESTADO ANTES DO REPLAY")
print("=" * 40)

for brick_size in BRICK_SIZES:
    state = renko_service.engines[
        brick_size
    ].state

    print(
        f"{brick_size}R | "
        f"open={state.open} | "
        f"last={state.last}"
    )


bootstrap_service = IntradayBootstrapService(
    tick_repository=tick_repository,
    renko_service=renko_service,
)


today = date.today().isoformat()


print()
print("REPLAY DO DIA")
print("=" * 40)

print("data :", today)


result = bootstrap_service.replay_day(
    symbol=HISTORICAL_SYMBOL,
    target_date=today,
    source_type="FUTURES",
    price_source="last",
)


print()
print("RESULTADO")
print("=" * 40)

print(
    "processed_ticks   :",
    result["processed_ticks"],
)

print(
    "last_timestamp_ms :",
    result["last_timestamp_ms"],
)


print()
print("ESTADO DEPOIS DO REPLAY")
print("=" * 40)

for brick_size in BRICK_SIZES:
    state = renko_service.engines[
        brick_size
    ].state

    print(
        f"{brick_size}R | "
        f"open={state.open} | "
        f"last={state.last}"
    )