from market.intraday_tick import IntradayTick
from market.realtime_tick import RealtimeTick


def realtime_to_intraday_tick(
    tick: RealtimeTick,
    source_type: str = "CFD",
    source_transition: bool = False,
) -> IntradayTick:

    return IntradayTick(
        timestamp_ms=int(tick.timestamp_ms),

        price=float(tick.price),

        bid=float(tick.bid),
        ask=float(tick.ask),
        last=float(tick.last),
        spread=float(tick.spread),

        volume=None,
        volume_real=None,
        flags=None,
        is_auction=None,

        buy_qty=None,
        sell_qty=None,

        buy_financial=None,
        sell_financial=None,

        source_type=source_type,
        source_symbol=tick.symbol,
        price_source=tick.source_price,
        
        source_transition=source_transition,
    )

def mt5_history_to_intraday_tick(
    tick,
    symbol: str,
    source_type: str = "FUTURES",
    price_source: str = "last",
) -> IntradayTick:

    if price_source not in {
        "bid",
        "ask",
        "last",
    }:
        raise ValueError(
            f"price_source inválido: "
            f"{price_source}"
        )

    raw_price = float(
        tick[price_source]
    )

    bid = float(
        tick["bid"]
    )

    ask = float(
        tick["ask"]
    )

    last = float(
        tick["last"]
    )

    spread = (
        ask - bid
        if bid > 0 and ask > 0
        else None
    )

    return IntradayTick(
        timestamp_ms=int(
            tick["time_msc"]
        ),

        price=raw_price,

        bid=bid,
        ask=ask,
        last=last,
        spread=spread,

        volume=float(
            tick["volume"]
        ),

        volume_real=float(
            tick["volume_real"]
        ),

        flags=int(
            tick["flags"]
        ),

        is_auction=None,

        buy_qty=None,
        sell_qty=None,

        buy_financial=None,
        sell_financial=None,

        source_type=source_type,
        source_symbol=symbol,
        price_source=price_source,

        source_transition=False,
    )