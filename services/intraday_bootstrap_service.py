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

        Mantido para compatibilidade com o fluxo histórico.
        """

        ticks = self.tick_repository.get_ticks_by_day(
            symbol,
            target_date,
        )

        return self.replay_ticks(
            ticks=ticks,
            symbol=symbol,
            source_type=source_type,
            price_source=price_source,
        )

    def replay_ticks(
        self,
        ticks,
        symbol: str,
        source_type: str,
        price_source: str,
    ) -> dict:
        """
        Reprocessa uma sequência de ticks já carregada.

        Os ticks NÃO são persistidos individualmente
        no banco intraday.

        O objetivo do bootstrap é:

        1. carregar o estado Renko anterior;
        2. processar todos os ticks já ocorridos hoje;
        3. reconstruir o estado Renko atual.

        A persistência dos Renko deve ser tratada
        separadamente do processamento dos ticks.
        """

        processed = 0
        last_timestamp_ms = None

        for tick in ticks:

            intraday_tick = (
                historical_tick_to_intraday_tick(
                    tick=tick,
                    symbol=symbol,
                    source_type=source_type,
                    price_source=price_source,
                )
            )

            self.renko_service.process_intraday_tick(
                intraday_tick
            )

            processed += 1

            last_timestamp_ms = (
                intraday_tick.timestamp_ms
            )

        return {
            "processed_ticks": processed,
            "last_timestamp_ms":
                last_timestamp_ms,
        }