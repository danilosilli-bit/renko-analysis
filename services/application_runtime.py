from __future__ import annotations

from config.storage_config import HISTORICAL_RENKO_DB
from storage.renko_repository import RenkoRepository
from storage.sqlite_manager import SQLiteManager
from storage.intraday_storage import reset_intraday_storage

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

    def __init__(self) -> None:
        self.started = False
        self.historical_repository = None

    def _reset_intraday_storage(self) -> None:
        """
        Reset reconstructible intraday persistence before startup.

        Approved historical and trading persistence are not part
        of this reset.
        """
        reset_intraday_storage()

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

    def stop(self) -> None:
        """
        Stop the market/Renko runtime.

        Shutdown behavior will be migrated incrementally from
        api/app.py.
        """
        raise NotImplementedError(
            "ApplicationRuntime.stop() is not implemented yet."
        )