from __future__ import annotations


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
        # Runtime lifecycle state
        self.started = False

    def start(self) -> None:
        """
        Start the market/Renko runtime.

        The implementation will be migrated incrementally from
        api/app.py only after each responsibility has been reviewed.
        """
        raise NotImplementedError(
            "ApplicationRuntime.start() is not implemented yet."
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