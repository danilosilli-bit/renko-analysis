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

    source_price: str


def from_mt5_tick(
    symbol: str,
    tick: dict,
) -> RealtimeTick:

    bid = float(
        tick["bid"]
    )

    ask = float(
        tick["ask"]
    )

    last = float(
        tick.get(
            "last",
            0.0,
        )
    )

    # ========================================================
    # SELEÇÃO DA FONTE DE PREÇO
    #
    # FUTUROS / WIN:
    # LAST disponível -> usa LAST
    #
    # CFD / Bra50:
    # LAST = 0 -> usa BID
    # ========================================================

    if last > 0:

        price = last
        source_price = "last"

    else:

        price = bid
        source_price = "bid"

    return RealtimeTick(
        symbol=symbol,
        timestamp_ms=int(
            tick["time_msc"]
        ),
        price=price,
        bid=bid,
        ask=ask,
        spread=ask - bid,
        last=last,
        source_price=source_price,
    )