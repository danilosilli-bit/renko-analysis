from trading.operation_manager import (
    OperationManager,
)


def test_create_operation():

    manager = OperationManager()

    operation = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )

    assert operation.operation_id is not None

    assert operation.broker_id == "xp"
    assert operation.feed == "WIN"
    assert operation.symbol == "WINV26"
    assert operation.side == "BUY"
    assert operation.volume == 1.0

    assert operation.entry_price is None
    assert operation.mt5_ticket is None

    assert (
        operation.max_stop_price
        == 183540.0
    )

    assert (
        operation.current_stop_price
        == 183540.0
    )

    assert operation.status == "PENDING"


def test_multiple_operations_are_independent():

    manager = OperationManager()

    operation_1 = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )

    operation_2 = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183685.0,
    )

    assert (
        operation_1.operation_id
        != operation_2.operation_id
    )

    assert (
        operation_1.max_stop_price
        == 183540.0
    )

    assert (
        operation_2.max_stop_price
        == 183685.0
    )

    manager.update_current_stop(
        operation_1.operation_id,
        183700.0,
    )

    assert (
        operation_1.current_stop_price
        == 183700.0
    )

    assert (
        operation_2.current_stop_price
        == 183685.0
    )

    assert (
        operation_1.max_stop_price
        == 183540.0
    )

    assert (
        operation_2.max_stop_price
        == 183685.0
    )


def test_win_and_cfd_operations_are_independent():

    manager = OperationManager()

    win_operation = (
        manager.create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    cfd_operation = (
        manager.create_operation(
            broker_id="activtrades",
            feed="CFD",
            symbol="Bra50Oct26",
            side="SELL",
            volume=0.05,
            max_stop_price=184265.0,
        )
    )

    assert (
        win_operation.operation_id
        != cfd_operation.operation_id
    )

    assert win_operation.feed == "WIN"
    assert cfd_operation.feed == "CFD"

    assert (
        win_operation.max_stop_price
        == 183540.0
    )

    assert (
        cfd_operation.max_stop_price
        == 184265.0
    )


def test_mark_operation_open():

    manager = OperationManager()

    operation = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )

    manager.mark_open(
        operation_id=
            operation.operation_id,
        entry_price=183800.0,
        mt5_ticket=123456,
    )

    assert operation.status == "OPEN"

    assert (
        operation.entry_price
        == 183800.0
    )

    assert (
        operation.mt5_ticket
        == 123456
    )

    # O stop máximo não muda quando
    # recebemos os dados do broker.
    assert (
        operation.max_stop_price
        == 183540.0
    )


def test_mark_operation_closed():

    manager = OperationManager()

    operation = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )

    manager.mark_open(
        operation_id=
            operation.operation_id,
        entry_price=183800.0,
        mt5_ticket=123456,
    )

    manager.mark_closed(
        operation.operation_id
    )

    assert operation.status == "CLOSED"

    assert (
        manager.get_open_operations()
        == []
    )


def test_get_open_operations():

    manager = OperationManager()

    operation_1 = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )

    operation_2 = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183685.0,
    )

    operation_3 = manager.create_operation(
        broker_id="activtrades",
        feed="CFD",
        symbol="Bra50Oct26",
        side="SELL",
        volume=0.05,
        max_stop_price=184265.0,
    )

    manager.mark_closed(
        operation_2.operation_id
    )

    open_operations = (
        manager.get_open_operations()
    )

    assert len(open_operations) == 2

    assert operation_1 in open_operations
    assert operation_3 in open_operations

    assert (
        operation_2
        not in open_operations
    )


def test_max_stop_does_not_change_with_new_operation():

    manager = OperationManager()

    operation_1 = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )

    original_max_stop = (
        operation_1.max_stop_price
    )

    operation_2 = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183830.0,
    )

    assert (
        operation_1.max_stop_price
        == original_max_stop
    )

    assert (
        operation_1.max_stop_price
        == 183540.0
    )

    assert (
        operation_2.max_stop_price
        == 183830.0
    )