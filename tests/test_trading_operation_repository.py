from storage.trading_operation_repository import (
    TradingOperationRepository,
)

from trading.trading_operation import (
    TradingOperation,
)


def create_repository(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )

    return TradingOperationRepository(
        db_path=str(db_path)
    )


def create_operation():

    return TradingOperation(
        operation_id="op-test-001",
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        entry_price=None,
        max_stop_price=183540.0,
        current_stop_price=183540.0,
        mt5_order_ticket=None,
        mt5_position_ticket=None,
        status="PENDING",
    )


def test_save_and_get_operation(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    operation = create_operation()

    repository.save(
        operation
    )

    loaded = repository.get(
        operation.operation_id
    )

    assert loaded is not None

    assert (
        loaded.operation_id
        == "op-test-001"
    )

    assert loaded.broker_id == "xp"
    assert loaded.feed == "WIN"
    assert loaded.symbol == "WINV26"
    assert loaded.side == "BUY"
    assert loaded.volume == 1.0

    assert loaded.entry_price is None

    assert (
        loaded.mt5_order_ticket
        is None
    )

    assert (
        loaded.mt5_position_ticket
        is None
    )

    assert loaded.status == "PENDING"

    assert (
        loaded.max_stop_price
        == 183540.0
    )

    assert (
        loaded.current_stop_price
        == 183540.0
    )


def test_update_open_operation(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    operation = create_operation()

    repository.save(
        operation
    )

    operation.entry_price = 183800.0

    operation.mt5_order_ticket = (
        123456
    )

    operation.mt5_position_ticket = (
        987654
    )

    operation.status = "OPEN"

    repository.update(
        operation
    )

    loaded = repository.get(
        operation.operation_id
    )

    assert loaded.status == "OPEN"

    assert (
        loaded.entry_price
        == 183800.0
    )

    assert (
        loaded.mt5_order_ticket
        == 123456
    )

    assert (
        loaded.mt5_position_ticket
        == 987654
    )

    assert (
        loaded.max_stop_price
        == 183540.0
    )


def test_update_current_stop(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    operation = create_operation()

    repository.save(
        operation
    )

    result = (
        operation.update_current_stop(
            183700.0
        )
    )

    assert result is True

    repository.update(
        operation
    )

    loaded = repository.get(
        operation.operation_id
    )

    assert (
        loaded.current_stop_price
        == 183700.0
    )

    assert (
        loaded.max_stop_price
        == 183540.0
    )


def test_max_stop_is_immutable_in_update(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    operation = create_operation()

    repository.save(
        operation
    )

    # Simula até uma alteração acidental
    # no objeto em memória.
    operation.max_stop_price = (
        999999.0
    )

    operation.current_stop_price = (
        183700.0
    )

    repository.update(
        operation
    )

    loaded = repository.get(
        operation.operation_id
    )

    # O banco deve manter o valor
    # originalmente gravado.
    assert (
        loaded.max_stop_price
        == 183540.0
    )

    assert (
        loaded.current_stop_price
        == 183700.0
    )


def test_get_active_operations(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    pending = TradingOperation(
        operation_id="pending-001",
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        entry_price=None,
        max_stop_price=183540.0,
        current_stop_price=183540.0,
        mt5_order_ticket=None,
        mt5_position_ticket=None,
        status="PENDING",
    )

    opened = TradingOperation(
        operation_id="open-001",
        broker_id="activtrades",
        feed="CFD",
        symbol="Bra50Oct26",
        side="SELL",
        volume=0.05,
        entry_price=183800.0,
        max_stop_price=184265.0,
        current_stop_price=184100.0,
        mt5_order_ticket=654321,
        mt5_position_ticket=765432,
        status="OPEN",
    )

    closed = TradingOperation(
        operation_id="closed-001",
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        entry_price=183700.0,
        max_stop_price=183400.0,
        current_stop_price=183750.0,
        mt5_order_ticket=111111,
        mt5_position_ticket=222222,
        status="CLOSED",
    )

    repository.save(pending)
    repository.save(opened)
    repository.save(closed)

    active = (
        repository.get_active()
    )

    ids = {
        operation.operation_id
        for operation in active
    }

    assert ids == {
        "pending-001",
        "open-001",
    }


def test_closed_operation_remains_saved(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    operation = create_operation()

    repository.save(
        operation
    )

    operation.entry_price = 183800.0

    operation.mt5_order_ticket = (
        123456
    )

    operation.mt5_position_ticket = (
        987654
    )

    operation.status = "OPEN"

    repository.update(
        operation
    )

    operation.status = "CLOSED"

    repository.update(
        operation
    )

    loaded = repository.get(
        operation.operation_id
    )

    assert loaded is not None
    assert loaded.status == "CLOSED"

    assert (
        loaded.mt5_order_ticket
        == 123456
    )

    assert (
        loaded.mt5_position_ticket
        == 987654
    )

    assert (
        repository.get_active()
        == []
    )


def test_persistence_after_new_repository_instance(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )

    repository_1 = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )

    operation = create_operation()

    repository_1.save(
        operation
    )

    # Simula reinicialização da aplicação:
    # nova instância usando o mesmo banco.
    repository_2 = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )

    loaded = repository_2.get(
        operation.operation_id
    )

    assert loaded is not None

    assert (
        loaded.max_stop_price
        == 183540.0
    )

    assert (
        loaded.current_stop_price
        == 183540.0
    )

    assert (
        loaded.mt5_order_ticket
        is None
    )

    assert (
        loaded.mt5_position_ticket
        is None
    )

    assert loaded.status == "PENDING"
    