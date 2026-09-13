from config.storage_config import (
    INTRADAY_DIR,
    INTRADAY_TICKS_DB,
    INTRADAY_RENKO_DB,
)

from storage.sqlite_manager import SQLiteManager
from storage.intraday_tick_repository import IntradayTickRepository

from storage.intraday_renko_repository import (
    IntradayRenkoRepository,
)


class IntradayRepository:

    def __init__(self):
        INTRADAY_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.ticks_db = SQLiteManager(
            str(INTRADAY_TICKS_DB)
        )

        self.renko_db = SQLiteManager(
            str(INTRADAY_RENKO_DB)
        )

        self.tick_repository = IntradayTickRepository(
            self.ticks_db
        )

        self.renko_repository = (
            IntradayRenkoRepository(
                self.renko_db
            )
        )

    def prepare_symbol(self, symbol: str):
        self.tick_repository.create_table(
            symbol
        )

        self.renko_repository.create_renko_table(
            symbol
        )

    def reset(self):
        if INTRADAY_TICKS_DB.exists():
            INTRADAY_TICKS_DB.unlink()

        if INTRADAY_RENKO_DB.exists():
            INTRADAY_RENKO_DB.unlink()

        self.ticks_db = SQLiteManager(
            str(INTRADAY_TICKS_DB)
        )

        self.renko_db = SQLiteManager(
            str(INTRADAY_RENKO_DB)
        )

        self.tick_repository = IntradayTickRepository(
            self.ticks_db
        )

        self.renko_repository = (
            IntradayRenkoRepository(
                self.renko_db
            )
        )