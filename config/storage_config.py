from pathlib import Path


DATA_DIR = Path("data")

HISTORICAL_DIR = DATA_DIR / "historical"
INTRADAY_DIR = DATA_DIR / "intraday"


HISTORICAL_TICKS_DB = HISTORICAL_DIR / "ticks.db"
HISTORICAL_RENKO_DB = HISTORICAL_DIR / "renko.db"

INTRADAY_TICKS_DB = INTRADAY_DIR / "ticks.db"
INTRADAY_RENKO_DB = INTRADAY_DIR / "renko.db"