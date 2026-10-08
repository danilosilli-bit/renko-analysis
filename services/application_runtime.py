from __future__ import annotations

from config.storage_config import HISTORICAL_RENKO_DB
from storage.renko_repository import RenkoRepository
from storage.sqlite_manager import SQLiteManager
from storage.intraday_repository import IntradayRepository
from storage.intraday_storage import reset_intraday_storage
from services.renko_service import RenkoService

from ingestion.mt5_intraday_history_client import (
    MT5IntradayHistoryClient,
)
from services.intraday_tick_adapter import (
    mt5_history_to_intraday_tick,
)


class ApplicationRuntime:
    """
    Coordinates the application market/Renko lifecycle.

    Responsibilities:
    - startup orchestration
    - historical/bootstrap orchestration
    - WIN/CFD runtime initialization
    - realtime feed lifecycle
    - shutdown orchestration

    This class must not implement:
    - Renko calculation logic
    - MT5 communication logic
    - persistence logic
    - trading rules or order execution

    Those responsibilities remain in their existing components.
    """

    def __init__(
        self,
        historical_symbol: str,
        intraday_symbol: str,
        bootstrap_renko_service: RenkoService,
        xp_terminal_path: str,
    ) -> None:
        self.historical_symbol = historical_symbol
        self.intraday_symbol = intraday_symbol
        self.bootstrap_renko_service = bootstrap_renko_service
        self.xp_terminal_path = xp_terminal_path
        

        self.started = False
        self.historical_repository = None
        self.intraday_repository = None
        self.bootstrap_result = None

    def _reset_intraday_storage(self) -> None:
        """
        Reset the intraday storage used by the current session.

        The actual reset behavior remains implemented by the
        existing storage component.
        """
        reset_intraday_storage()

    def _prepare_intraday_repository(self) -> None:
        self.intraday_repository = IntradayRepository()

        self.intraday_repository.prepare_symbol(
            self.historical_symbol
        )

        self.intraday_repository.prepare_symbol(
            self.intraday_symbol
        )

    def _initialize_historical_renko(self) -> None:
        """
        Initialize the common Renko state from approved history.

        This happens before today's XP tick replay and before
        the WIN/CFD runtime bifurcation.
        """
        self.bootstrap_renko_service.initialize_from_history(
            historical_repository=self.historical_repository,
            intraday_repository=self.intraday_repository.renko_repository,
            historical_symbol=self.historical_symbol,
            intraday_symbol=self.historical_symbol,
            defer_persistence=True,
        )

    def _open_historical_repository(self) -> None:
        historical_db = SQLiteManager(
            str(HISTORICAL_RENKO_DB)
        )

        self.historical_repository = RenkoRepository(
            historical_db
        )

    def start(self) -> None:
        self._reset_intraday_storage()
        self._open_historical_repository()
        self._prepare_intraday_repository()
        self._initialize_historical_renko()

        today_ticks = self._fetch_today_xp_ticks()

        self.bootstrap_result = self._replay_today_xp_ticks(
            today_ticks
        )

    def stop(self) -> None:
        """
        Stop the market/Renko runtime.

        Shutdown behavior will be migrated incrementally from
        api/app.py.
        """
        raise NotImplementedError(
            "ApplicationRuntime.stop() is not implemented yet."
        )

    def _fetch_today_xp_ticks(self):
        client = MT5IntradayHistoryClient(
            terminal_path=self.xp_terminal_path
        )

        client.connect()

        try:
            return client.get_today_ticks(
                self.historical_symbol
            )
        finally:
            client.disconnect()

    def _replay_today_xp_ticks(self, today_ticks):
        processed_ticks = 0
        last_timestamp_ms = None

        for raw_tick in today_ticks:
            intraday_tick = mt5_history_to_intraday_tick(
                raw_tick,
                symbol=self.historical_symbol,
                source_type="FUTURES",
                price_source="last",
            )

            self.bootstrap_renko_service.process_intraday_tick(
                intraday_tick
            )

            processed_ticks += 1
            last_timestamp_ms = intraday_tick.timestamp_ms

        return {
            "processed_ticks": processed_ticks,
            "last_timestamp_ms": last_timestamp_ms,
        }