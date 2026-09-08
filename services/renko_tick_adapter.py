from market.realtime_tick import RealtimeTick


def realtime_to_renko_tick(tick: RealtimeTick) -> dict:
    """
    Converte RealtimeTick para o formato esperado pelo
    RenkoEngine existente.

    Para Bra50/Bra50Oct26 da ActivTrades:
    - MT5 LAST permanece 0.
    - BID é utilizado como preço analítico do Renko.
    """

    return {
        "symbol": tick.symbol,
        "timestamp_ms": tick.timestamp_ms,

        # Campo esperado pelo RenkoEngine.
        # Aqui representa o BID normalizado, não o LAST bruto do MT5.
        "last": tick.price,

        # Dados reais do book/feed.
        "bid": tick.bid,
        "ask": tick.ask,
        "spread": tick.spread,

        # Bra50 não fornece esses dados no tick atual.
        "volume": 0.0,
        "buy_qty": 0.0,
        "sell_qty": 0.0,
        "buy_financial": 0.0,
        "sell_financial": 0.0,

        # Metadados de origem.
        "price_source": tick.source_price,
        "mt5_last": tick.last,
    }