from dataclasses import dataclass


@dataclass(frozen=True)
class RealtimeTick:
    symbol: str
    timestamp_ms: int

    price: float

    bid: float
    ask: float
    spread: float

    last: float

    source_price: str = "bid"


def from_mt5_tick(
    symbol: str,
    tick: dict,
) -> RealtimeTick:

    bid = float(tick["bid"])
    ask = float(tick["ask"])
    last = float(tick.get("last", 0.0))

    return RealtimeTick(
        symbol=symbol,
        timestamp_ms=int(tick["time_msc"]),
        price=bid,
        bid=bid,
        ask=ask,
        spread=ask - bid,
        last=last,
        source_price="bid",
    )