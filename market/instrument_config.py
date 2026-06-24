class InstrumentConfig:

    def __init__(
        self,
        symbol,
        tick_size,
        price_decimals,
        renko_sizes=None
    ):
        self.symbol = symbol
        self.tick_size = tick_size
        self.price_decimals = price_decimals
        self.renko_sizes = renko_sizes or []

    def get_brick_distance(self, brick_size):
        return brick_size * self.tick_size

    def get_effective_brick_distance(self, brick_size):
        return (brick_size * self.tick_size) - self.tick_size
    
    def has_renko_sizes(self):
        return len(self.renko_sizes) > 0
    
    def round_price(self, price):
        return round(
            price,
            self.price_decimals
        )

    @staticmethod
    def normalize_symbol(symbol):
        symbol = symbol.upper()

        if symbol.startswith("WIN"):
            return "WIN"

        if symbol.startswith("WDO"):
            return "WDO"

        return symbol

    @classmethod
    def from_symbol(cls, symbol):
        normalized_symbol = cls.normalize_symbol(symbol)
        try:
            return MARKET_CONFIG[normalized_symbol]
        except KeyError:
            raise ValueError(
                f"Symbol '{symbol}' not configured."
                f"Normalized as '{normalized_symbol}'."
            )

MARKET_CONFIG = {
    "WIN": InstrumentConfig(
        symbol="WIN",
        tick_size=5,
        price_decimals=0,
        renko_sizes=[10, 15, 25, 30, 45, 65]
    ),
    "WDO": InstrumentConfig(
        symbol="WDO",
        tick_size=0.5,
        price_decimals=2,
        renko_sizes=[2, 3, 5, 6, 8, 10]
    ),
    "PETR4": InstrumentConfig(
        symbol="PETR4",
        tick_size=0.01,
        price_decimals=2,
        renko_sizes=[7, 10, 15]
    ),
    "VALE3": InstrumentConfig(
        symbol="VALE3",
        tick_size=0.01,
        price_decimals=2,
        renko_sizes=[7, 10, 15]
    ),
    "ITUB4": InstrumentConfig(
        symbol="ITUB4",
        tick_size=0.01,
        price_decimals=2,
        renko_sizes=[7, 10, 15]
    ),    
    "EURUSD": InstrumentConfig(
        symbol="EURUSD",
        tick_size=0.00001,
        price_decimals=5,
        renko_sizes=[]
    ),
}