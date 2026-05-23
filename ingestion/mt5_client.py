import MetaTrader5 as mt5


class MT5Client:

    def __init__(self, login=None, server=None):
        self.login = login
        self.server = server
        self.connected = False

    def connect(self):
        """Connect to MT5 terminal"""
        if not mt5.initialize(login=self.login, server=self.server):
            raise Exception(f"MT5 connection failed: {mt5.last_error()}")

        self.connected = True

    def disconnect(self):
        """Shutdown MT5 connection"""
        mt5.shutdown()
        self.connected = False

    def get_terminal_info(self):
        """Return terminal info as dict"""
        info = mt5.terminal_info()
        return info._asdict() if info else None

    def get_ticks(self, symbol, date_from, count=-1, flags=mt5.COPY_TICKS_TRADE):
        """Fetch raw ticks from MT5"""
        ticks = mt5.copy_ticks_from(
            symbol,
            date_from,
            count,
            flags
        )

        return ticks