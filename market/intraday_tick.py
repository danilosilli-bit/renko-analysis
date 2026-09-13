from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class IntradayTick:
    timestamp_ms: int

    # preço efetivamente usado pelo Renko
    price: float

    # dados básicos de mercado
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    spread: Optional[float] = None

    # informações de negociação
    volume: Optional[float] = None
    volume_real: Optional[float] = None
    flags: Optional[int] = None
    is_auction: Optional[int] = None

    buy_qty: Optional[float] = None
    sell_qty: Optional[float] = None

    buy_financial: Optional[float] = None
    sell_financial: Optional[float] = None

    # origem do dado
    source_type: str = ""
    source_symbol: str = ""
    price_source: str = ""

    source_transition: bool = False