def serialize_state(state):

    if state is None:
        return None

    return {
        "symbol":
            state.symbol,

        "brick_size":
            state.brick_size,

        "open_time":
            state.open_time,

        "open":
            state.open,

        "last":
            state.last,

        "high":
            state.high,

        "low":
            state.low,

        "direction":
            state.direction,

        "volume":
            state.volume,

        "buy_qty":
            state.buy_qty,

        "sell_qty":
            state.sell_qty,

        "buy_financial":
            state.buy_financial,

        "sell_financial":
            state.sell_financial,

        "trades_count":
            state.trades_count,
    }


def serialize_tick(tick):

    if tick is None:
        return None

    return {
        "symbol":
            tick.symbol,

        "time_msc":
            tick.timestamp_ms,

        "price":
            tick.price,

        "bid":
            tick.bid,

        "ask":
            tick.ask,

        "last":
            tick.last,

        "spread":
            tick.spread,

        "price_source":
            tick.source_price,
    }
