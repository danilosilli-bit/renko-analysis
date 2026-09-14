from datetime import datetime, time, timezone

import MetaTrader5 as mt5


class MT5IntradayHistoryClient:

    def __init__(
        self,
        terminal_path: str,
    ):
        self.terminal_path = terminal_path
        self.connected = False

    def connect(self):

        if self.connected:
            return

        if not mt5.initialize(
            path=self.terminal_path
        ):
            raise RuntimeError(
                f"Falha ao conectar ao MT5: "
                f"{mt5.last_error()}"
            )

        self.connected = True

    def disconnect(self):

        if not self.connected:
            return

        mt5.shutdown()

        self.connected = False

    def get_today_ticks(
        self,
        symbol: str,
    ):
        """
        Retorna os ticks válidos do dia atual
        em ordem cronológica.
        """

        if not self.connected:
            raise RuntimeError(
                "MT5 não conectado."
            )

        now = datetime.now(
            timezone.utc
        )

        start = datetime.combine(
            now.date(),
            time.min,
            tzinfo=timezone.utc,
        )

        ticks = mt5.copy_ticks_range(
            symbol,
            start,
            now,
            mt5.COPY_TICKS_ALL,
        )

        if ticks is None:
            raise RuntimeError(
                f"Erro ao buscar ticks de "
                f"{symbol}: {mt5.last_error()}"
            )

        valid_ticks = [
            tick
            for tick in ticks
            if float(tick["last"]) > 0
        ]

        return valid_ticks