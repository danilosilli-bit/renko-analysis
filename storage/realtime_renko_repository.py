class RealtimeRenkoRepository:

    def __init__(
        self,
        historical_repository,
        intraday_repository,
        historical_symbol,
        intraday_symbol,
        defer_persistence: bool = False,
    ):
        self.historical_repository = (
            historical_repository
        )

        self.intraday_repository = (
            intraday_repository
        )

        self.historical_symbol = (
            historical_symbol
        )

        self.intraday_symbol = (
            intraday_symbol
        )

        self.defer_persistence = (
            defer_persistence
        )

        self.bricks = []

        self.source_transition = False


    def set_source_transition(
        self,
        value: bool,
    ) -> None:
        self.source_transition = bool(
            value
        )


    def get_state(
        self,
        symbol,
        brick_size,
    ):
        return (
            self.historical_repository
            .get_state(
                self.historical_symbol,
                brick_size,
            )
        )


    def get_last_closed_brick(
        self,
        symbol,
        brick_size,
    ):
        return (
            self.historical_repository
            .get_last_closed_brick(
                self.historical_symbol,
                brick_size,
            )
        )


    def save_brick(
        self,
        symbol,
        brick,
    ):
        brick_to_save = brick.copy()

        brick_to_save[
            "source_transition"
        ] = self.source_transition

        # Primeiro mantém o brick em memória.
        self.bricks.append(
            brick_to_save
        )

        # No realtime normal continua gravando imediatamente.
        # No bootstrap, com defer_persistence=True,
        # apenas acumula em memória.
        if not self.defer_persistence:

            self.intraday_repository.save_brick(
                self.intraday_symbol,
                brick_to_save,
            )

    def persist_bricks(
        self,
        target_symbols,
    ):
        for brick in self.bricks:

            for target_symbol in target_symbols:

                self.intraday_repository.save_brick(
                    target_symbol,
                    brick,
                )

    def save_state(
        self,
        state,
    ):
        pass