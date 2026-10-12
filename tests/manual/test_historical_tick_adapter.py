from config.storage_config import HISTORICAL_TICKS_DB

from storage.sqlite_manager import SQLiteManager

from services.historical_tick_adapter import (
    historical_tick_to_intraday_tick,
)


SYMBOL = "WINV26"


db = SQLiteManager(
    str(HISTORICAL_TICKS_DB)
)

table_name = f"ticks_{SYMBOL.lower()}"


rows = db.execute(
    f"""
    SELECT *
    FROM {table_name}
    ORDER BY id DESC
    LIMIT 1
    """
)

tick = dict(rows[0])


print()
print("TICK HISTÓRICO")
print("=" * 40)

print("timestamp_ms :", tick["timestamp_ms"])
print("last         :", tick["last"])
print("bid          :", tick["bid"])
print("ask          :", tick["ask"])
print("volume       :", tick["volume"])


intraday_tick = historical_tick_to_intraday_tick(
    tick=tick,
    symbol=SYMBOL,
    source_type="FUTURES",
    price_source="last",
)


print()
print("INTRADAY TICK")
print("=" * 40)

print("timestamp_ms :", intraday_tick.timestamp_ms)
print("price        :", intraday_tick.price)
print("bid          :", intraday_tick.bid)
print("ask          :", intraday_tick.ask)
print("last         :", intraday_tick.last)
print("spread       :", intraday_tick.spread)


print()
print("SOURCE")
print("=" * 40)

print("source_type   :", intraday_tick.source_type)
print("source_symbol :", intraday_tick.source_symbol)
print("price_source  :", intraday_tick.price_source)