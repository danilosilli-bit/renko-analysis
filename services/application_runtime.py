from __future__ import annotations

from config.storage_config import HISTORICAL_RENKO_DB
from storage.renko_repository import RenkoRepository
from storage.sqlite_manager import SQLiteManager
from storage.intraday_repository import IntradayRepository
from storage.intraday_storage import reset_intraday_storage
from services.renko_service import RenkoService



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
    ) -> None:
        self.historical_symbol = historical_symbol
        self.intraday_symbol = intraday_symbol
        self.bootstrap_renko_service = bootstrap_renko_service
        

        self.started = False
        self.historical_repository = None
        self.intraday_repository = None

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
        """
        Start the market/Renko runtime.

        Responsibilities are being migrated incrementally from
        api/app.py.

        The runtime is not considered fully started until the complete
        startup lifecycle has been migrated.
        """
        self._reset_intraday_storage()
        self._open_historical_repository()
        self._prepare_intraday_repository()
        self._initialize_historical_renko()

    def stop(self) -> None:
        """
        Stop the market/Renko runtime.

        Shutdown behavior will be migrated incrementally from
        api/app.py.
        """
        raise NotImplementedError(
            "ApplicationRuntime.stop() is not implemented yet."
        )