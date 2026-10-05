from trading.trading_operation import (
    TradingOperation,
)


def create_buy_operation():

    return TradingOperation(
        operation_id="op-buy-001",
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        entry_price=183800.0,
        max_stop_price=183540.0,
        current_stop_price=183540.0,
        mt5_ticket=123456,
        status="OPEN",
    )


def create_sell_operation():

    return TradingOperation(
        operation_id="op-sell-001",
        broker_id="activtrades",
        feed="CFD",
        symbol="Bra50Oct26",
        side="SELL",
        volume=0.05,
        entry_price=183800.0,
        max_stop_price=184265.0,
        current_stop_price=184265.0,
        mt5_ticket=654321,
        status="OPEN",
    )


def test_buy_stop_can_move_up():

    operation = create_buy_operation()

    result = operation.update_current_stop(
        183650.0
    )

    assert result is True

    assert (
        operation.current_stop_price
        == 183650.0
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )


def test_buy_stop_cannot_move_back_down():

    operation = create_buy_operation()

    operation.update_current_stop(
        183700.0
    )

    result = operation.update_current_stop(
        183650.0
    )

    assert result is False

    assert (
        operation.current_stop_price
        == 183700.0
    )


def test_buy_stop_cannot_go_below_max_stop():

    operation = create_buy_operation()

    result = operation.update_current_stop(
        183500.0
    )

    assert result is False

    assert (
        operation.current_stop_price
        == 183540.0
    )


def test_sell_stop_can_move_down():

    operation = create_sell_operation()

    result = operation.update_current_stop(
        184100.0
    )

    assert result is True

    assert (
        operation.current_stop_price
        == 184100.0
    )

    assert (
        operation.max_stop_price
        == 184265.0
    )


def test_sell_stop_cannot_move_back_up():

    operation = create_sell_operation()

    operation.update_current_stop(
        184100.0
    )

    result = operation.update_current_stop(
        184150.0
    )

    assert result is False

    assert (
        operation.current_stop_price
        == 184100.0
    )


def test_sell_stop_cannot_go_above_max_stop():

    operation = create_sell_operation()

    result = operation.update_current_stop(
        184300.0
    )

    assert result is False

    assert (
        operation.current_stop_price
        == 184265.0
    )


def test_buy_max_stop_remains_frozen():

    operation = create_buy_operation()

    original_max_stop = (
        operation.max_stop_price
    )

    operation.update_current_stop(
        183650.0
    )

    operation.update_current_stop(
        183750.0
    )

    operation.update_current_stop(
        183850.0
    )

    assert (
        operation.max_stop_price
        == original_max_stop
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )

    assert (
        operation.current_stop_price
        == 183850.0
    )


def test_sell_max_stop_remains_frozen():

    operation = create_sell_operation()

    original_max_stop = (
        operation.max_stop_price
    )

    operation.update_current_stop(
        184150.0
    )

    operation.update_current_stop(
        184000.0
    )

    operation.update_current_stop(
        183900.0
    )

    assert (
        operation.max_stop_price
        == original_max_stop
    )

    assert (
        operation.max_stop_price
        == 184265.0
    )

    assert (
        operation.current_stop_price
        == 183900.0
    )