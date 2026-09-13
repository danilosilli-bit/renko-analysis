from services.historical_tick_adapter import (
    historical_tick_to_intraday_tick,
)


class IntradayBootstrapService:

    def __init__(
        self,
        tick_repository,
        renko_service,
    ):
        self.tick_repository = tick_repository
        self.renko_service = renko_service

    def replay_day(
        self,
        symbol: str,
        target_date: str,
        source_type: str,
        price_source: str,
    ) -> dict:
        """
        Reprocessa os ticks já ocorridos no dia informado,
        partindo do estado Renko previamente carregado.

        O RenkoService deve ter sido inicializado antes com
        initialize_from_history().
        """

        ticks = self.tick_repository.get_ticks_by_day(
            symbol,
            target_date,
        )

        processed = 0
        last_timestamp_ms = None

        for tick in ticks:
            intraday_tick = historical_tick_to_intraday_tick(
                tick=tick,
                symbol=symbol,
                source_type=source_type,
                price_source=price_source,
            )

            self.renko_service.process_intraday_tick(
                intraday_tick
            )

            processed += 1
            last_timestamp_ms = intraday_tick.timestamp_ms

        return {
            "processed_ticks": processed,
            "last_timestamp_ms": last_timestamp_ms,
        }