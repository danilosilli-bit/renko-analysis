from trading.order_guard import OrderGuard


def test_buy_allowed():

    def signal_provider(feed):

        assert feed == "WIN"

        return {
            "ready": True,
            "direction": "BUY",
            "can_buy": True,
            "can_sell": False,
            "max_stop_price": 183955.0,
        }

    guard = OrderGuard(
        signal_provider
    )

    result = guard.validate_entry(
        feed="WIN",
        side="BUY",
    )

    assert result["allowed"] is True
    assert result["direction"] == "BUY"
    assert (
        result["max_stop_price"]
        == 183955.0
    )


def test_sell_blocked_when_signal_is_buy():

    def signal_provider(feed):

        return {
            "ready": True,
            "direction": "BUY",
            "can_buy": True,
            "can_sell": False,
            "max_stop_price": 183955.0,
        }

    guard = OrderGuard(
        signal_provider
    )

    result = guard.validate_entry(
        feed="WIN",
        side="SELL",
    )

    assert result["allowed"] is False
    assert result["direction"] == "BUY"


def test_sell_allowed():

    def signal_provider(feed):

        assert feed == "CFD"

        return {
            "ready": True,
            "direction": "SELL",
            "can_buy": False,
            "can_sell": True,
            "max_stop_price": 184430.0,
        }

    guard = OrderGuard(
        signal_provider
    )

    result = guard.validate_entry(
        feed="CFD",
        side="SELL",
    )

    assert result["allowed"] is True
    assert result["direction"] == "SELL"
    assert (
        result["max_stop_price"]
        == 184430.0
    )


def test_buy_blocked_when_signal_is_sell():

    def signal_provider(feed):

        return {
            "ready": True,
            "direction": "SELL",
            "can_buy": False,
            "can_sell": True,
            "max_stop_price": 184430.0,
        }

    guard = OrderGuard(
        signal_provider
    )

    result = guard.validate_entry(
        feed="CFD",
        side="BUY",
    )

    assert result["allowed"] is False
    assert result["direction"] == "SELL"


def test_blocks_when_signal_not_ready():

    def signal_provider(feed):

        return {
            "ready": False,
            "direction": None,
            "can_buy": False,
            "can_sell": False,
            "max_stop_price": None,
        }

    guard = OrderGuard(
        signal_provider
    )

    result = guard.validate_entry(
        feed="WIN",
        side="BUY",
    )

    assert result["allowed"] is False
    assert (
        result["reason"]
        == "Sinal 30R não está pronto."
    )


def test_blocks_when_provider_fails():

    def signal_provider(feed):

        raise RuntimeError(
            "Falha simulada"
        )

    guard = OrderGuard(
        signal_provider
    )

    result = guard.validate_entry(
        feed="WIN",
        side="BUY",
    )

    assert result["allowed"] is False
    assert (
        result["reason"]
        == "Falha ao obter sinal 30R."
    )


def test_blocks_when_signal_is_missing():

    def signal_provider(feed):

        return None

    guard = OrderGuard(
        signal_provider
    )

    result = guard.validate_entry(
        feed="WIN",
        side="BUY",
    )

    assert result["allowed"] is False
    assert (
        result["reason"]
        == "Sinal 30R indisponível."
    )