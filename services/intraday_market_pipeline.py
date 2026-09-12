from market.intraday_tick import IntradayTick


class IntradayMarketPipeline:
    """
    Pipeline intraday:

    1. persiste o tick recebido;
    2. envia o tick ao RenkoService.
    """

    def __init__(
        self,
        tick_repository,
        renko_service,
        symbol: str,
    ):
        self.tick_repository = tick_repository
        self.renko_service = renko_service
        self.symbol = symbol

    def process_tick(
        self,
        tick: IntradayTick,
    ) -> None:

        self.tick_repository.save_tick(
            self.symbol,
            tick,
        )

        self.renko_service.process_intraday_tick(
            tick
        )