from market.intraday_tick import IntradayTick


def intraday_to_renko_tick(
    tick: IntradayTick,
):
    """
    Converte IntradayTick para o formato
    esperado pelo RenkoEngine.

    No banco intraday, campos indisponíveis
    podem permanecer como None.

    No RenkoEngine, métricas acumulativas
    precisam ser numéricas.
    """

    return {
        "timestamp_ms": int(
            tick.timestamp_ms
        ),

        # O RenkoEngine usa a chave "last"
        # como preço analítico.
        #
        # CFD:
        #   tick.price = BID
        #
        # WIN:
        #   tick.price = LAST
        "last": float(
            tick.price
        ),

        "volume": (
            float(tick.volume)
            if tick.volume is not None
            else 0.0
        ),

        "buy_qty": (
            float(tick.buy_qty)
            if tick.buy_qty is not None
            else 0.0
        ),

        "sell_qty": (
            float(tick.sell_qty)
            if tick.sell_qty is not None
            else 0.0
        ),

        "buy_financial": (
            float(tick.buy_financial)
            if tick.buy_financial is not None
            else 0.0
        ),

        "sell_financial": (
            float(tick.sell_financial)
            if tick.sell_financial is not None
            else 0.0
        ),
    }