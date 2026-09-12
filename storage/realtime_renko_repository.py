class RealtimeRenkoRepository:
    """
    Adapter de repository para o RenkoEngine em modo realtime.

    Responsabilidades:

    - lê o estado inicial do histórico oficial;
    - lê o último brick fechado do histórico oficial;
    - grava novos bricks somente no banco intraday;
    - não persiste o estado aberto intraday.

    O estado aberto permanece exclusivamente em memória
    dentro do RenkoEngine.
    """

    def __init__(
        self,
        historical_repository,
        intraday_repository,
        historical_symbol,
        intraday_symbol,
    ):
        self.historical_repository = historical_repository
        self.intraday_repository = intraday_repository

        self.historical_symbol = historical_symbol
        self.intraday_symbol = intraday_symbol

        self.bricks = []

    def get_state(
        self,
        symbol,
        brick_size,
    ):
        return self.historical_repository.get_state(
            self.historical_symbol,
            brick_size,
        )

    def get_last_closed_brick(
        self,
        symbol,
        brick_size,
    ):
        return self.historical_repository.get_last_closed_brick(
            self.historical_symbol,
            brick_size,
        )

    def save_brick(
        self,
        symbol,
        brick,
    ):
        self.intraday_repository.save_brick(
            self.intraday_symbol,
            brick,
        )

        self.bricks.append(
            brick.copy()
        )
        
    def save_state(
        self,
        state,
    ):
        # Intencionalmente vazio.
        #
        # O estado aberto intraday não é persistido.
        # Ele permanece apenas em memória no RenkoEngine.
        pass