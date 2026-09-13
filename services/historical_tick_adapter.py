import numpy as np

from market.intraday_tick import IntradayTick


def _to_timestamp_ms(value) -> int:
    """
    Converte o timestamp histórico para epoch em milissegundos.

    O TickRepository atualmente retorna timestamp_ms
    como np.datetime64.
    """

    if isinstance(value, np.datetime64):
        return int(
            value.astype("datetime64[ms]").astype(np.int64)
        )

    return int(
        np.datetime64(value)
        .astype("datetime64[ms]")
        .astype(np.int64)
    )


def historical_tick_to_intraday_tick(
    tick: dict,
    symbol: str,
    source_type: str,
    price_source: str,
) -> IntradayTick:
    """
    Converte um tick da fonte histórica para o formato comum
    utilizado pelo processamento intraday.

    O campo utilizado como preço analítico é configurável
    através de price_source.

    Exemplos:
        price_source="last"
        price_source="bid"
        price_source="ask"
    """

    if price_source not in tick:
        raise ValueError(
            f"price_source '{price_source}' não existe no tick"
        )

    raw_price = tick.get(price_source)

    if raw_price is None:
        raise ValueError(
            f"price_source '{price_source}' está vazio"
        )

    bid = (
        float(tick["bid"])
        if tick.get("bid") is not None
        else None
    )

    ask = (
        float(tick["ask"])
        if tick.get("ask") is not None
        else None
    )

    last = (
        float(tick["last"])
        if tick.get("last") is not None
        else None
    )

    spread = None

    return IntradayTick(
        timestamp_ms=_to_timestamp_ms(
            tick["timestamp_ms"]
        ),

        price=float(raw_price),

        bid=bid,
        ask=ask,
        last=last,
        spread=spread,

        volume=(
            float(tick["volume"])
            if tick.get("volume") is not None
            else None
        ),

        volume_real=(
            float(tick["volume_real"])
            if tick.get("volume_real") is not None
            else None
        ),

        flags=(
            int(tick["flags"])
            if tick.get("flags") is not None
            else None
        ),

        is_auction=(
            int(tick["is_auction"])
            if tick.get("is_auction") is not None
            else None
        ),

        buy_qty=(
            float(tick["buy_qty"])
            if tick.get("buy_qty") is not None
            else None
        ),

        sell_qty=(
            float(tick["sell_qty"])
            if tick.get("sell_qty") is not None
            else None
        ),

        buy_financial=(
            float(tick["buy_financial"])
            if tick.get("buy_financial") is not None
            else None
        ),

        sell_financial=(
            float(tick["sell_financial"])
            if tick.get("sell_financial") is not None
            else None
        ),

        source_type=source_type,
        source_symbol=symbol,
        price_source=price_source,
    )