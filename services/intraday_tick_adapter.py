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