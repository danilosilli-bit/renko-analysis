class InstrumentConfig:

    def __init__(
        self,
        symbol,
        tick_size,
        price_decimals
    ):
        self.symbol = symbol
        self.tick_size = tick_size
        self.price_decimals = price_decimals

    def get_brick_distance(
        self,
        brick_size
    ):
        return brick_size * self.tick_size

    @classmethod
    def from_symbol(cls, symbol):
        try:
            return MARKET_CONFIG[symbol]
        except KeyError:
            raise ValueError(
                f"Symbol '{symbol}' not configured."
            )


MARKET_CONFIG = {
    "WIN": InstrumentConfig(
        symbol="WIN",
        tick_size=5,
        price_decimals=0
    ),
    "WDO": InstrumentConfig(
        symbol="WDO",
        tick_size=0.5,
        price_decimals=2
    ),
    "PETR4": InstrumentConfig(
        symbol="PETR4",
        tick_size=0.01,
        price_decimals=2
    ),
    "EURUSD": InstrumentConfig(
        symbol="EURUSD",
        tick_size=0.00001,
        price_decimals=5
    ),
}