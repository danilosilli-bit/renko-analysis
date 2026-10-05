from storage.trading_operation_repository import (
    TradingOperationRepository,
)

from trading.operation_manager import (
    OperationManager,
)


def create_manager(
    db_path,
):

    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )

    manager = OperationManager(
        repository=repository
    )

    return manager


def test_create_operation_is_persisted(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )

    manager = create_manager(
        db_path
    )

    operation = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )


    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )

    loaded = repository.get(
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

    assert loaded.status == "PENDING"


def test_mark_open_is_persisted(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )

    manager = create_manager(
        db_path
    )

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
        mt5_order_ticket=123456,
        mt5_position_ticket=123456,
    )


    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
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
        loaded.max_stop_price
        == 183540.0
    )


def test_current_stop_is_persisted(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )

    manager = create_manager(
        db_path
    )

    operation = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )


    result = manager.update_current_stop(
        operation_id=
            operation.operation_id,
        new_stop_price=183700.0,
    )


    assert result is True


    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
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


def test_restart_restores_open_operation(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )


    # ==================================
    # PRIMEIRA EXECUÇÃO DA PLATAFORMA
    # ==================================

    manager_1 = create_manager(
        db_path
    )

    operation = manager_1.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )

    manager_1.mark_open(
        operation_id=
            operation.operation_id,
        entry_price=183800.0,
        mt5_order_ticket=123456,
        mt5_position_ticket=123456,
    )

    manager_1.update_current_stop(
        operation_id=
            operation.operation_id,
        new_stop_price=183700.0,
    )


    # ==================================
    # SIMULA REINÍCIO DA PLATAFORMA
    # ==================================

    manager_2 = create_manager(
        db_path
    )


    restored = (
        manager_2.get_operation(
            operation.operation_id
        )
    )


    assert restored is not None

    assert restored.status == "OPEN"

    assert (
        restored.entry_price
        == 183800.0
    )

    assert (
        restored.mt5_order_ticket
        == 123456
    )

    assert (
        restored.max_stop_price
        == 183540.0
    )

    assert (
        restored.current_stop_price
        == 183700.0
    )


def test_restart_restores_multiple_operations(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )


    manager_1 = create_manager(
        db_path
    )


    operation_1 = (
        manager_1.create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )


    operation_2 = (
        manager_1.create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183685.0,
        )
    )


    operation_3 = (
        manager_1.create_operation(
            broker_id="activtrades",
            feed="CFD",
            symbol="Bra50Oct26",
            side="SELL",
            volume=0.05,
            max_stop_price=184265.0,
        )
    )


    manager_1.mark_open(
        operation_1.operation_id,
        entry_price=183800.0,
        mt5_order_ticket=111111,
        mt5_position_ticket=111111,
    )


    manager_1.mark_open(
        operation_2.operation_id,
        entry_price=183900.0,
        mt5_order_ticket=222222,
        mt5_position_ticket=222222,
    )


    manager_1.mark_open(
        operation_3.operation_id,
        entry_price=183750.0,
        mt5_order_ticket=333333,
        mt5_position_ticket=333333,
    )


    # ==================================
    # REINÍCIO
    # ==================================

    manager_2 = create_manager(
        db_path
    )


    restored_operations = (
        manager_2.get_open_operations()
    )


    assert len(
        restored_operations
    ) == 3


    restored_1 = (
        manager_2.get_operation(
            operation_1.operation_id
        )
    )

    restored_2 = (
        manager_2.get_operation(
            operation_2.operation_id
        )
    )

    restored_3 = (
        manager_2.get_operation(
            operation_3.operation_id
        )
    )


    assert (
        restored_1.max_stop_price
        == 183540.0
    )

    assert (
        restored_2.max_stop_price
        == 183685.0
    )

    assert (
        restored_3.max_stop_price
        == 184265.0
    )


def test_closed_operation_is_not_restored_as_active(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )


    manager_1 = create_manager(
        db_path
    )


    operation = manager_1.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )


    manager_1.mark_open(
        operation.operation_id,
        entry_price=183800.0,
        mt5_order_ticket=123456,
        mt5_position_ticket=123456,
    )


    manager_1.mark_closed(
        operation.operation_id
    )


    # ==================================
    # REINÍCIO
    # ==================================

    manager_2 = create_manager(
        db_path
    )


    restored = (
        manager_2.get_operation(
            operation.operation_id
        )
    )


    assert restored is None

    assert (
        manager_2.get_open_operations()
        == []
    )


    # Mas continua registrado
    # no histórico do SQLite.

    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )

    historical = repository.get(
        operation.operation_id
    )

    assert historical is not None

    assert (
        historical.status
        == "CLOSED"
    )

def test_failed_operation_is_persisted(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )


    manager = create_manager(
        db_path
    )


    operation = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )


    assert operation.status == "PENDING"


    manager.mark_failed(
        operation.operation_id
    )


    assert operation.status == "FAILED"


    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )


    loaded = repository.get(
        operation.operation_id
    )


    assert loaded is not None

    assert (
        loaded.status
        == "FAILED"
    )

    assert (
        loaded.max_stop_price
        == 183540.0
    )


def test_failed_operation_is_not_restored_as_active(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )


    # ==================================
    # PRIMEIRA EXECUÇÃO
    # ==================================

    manager_1 = create_manager(
        db_path
    )


    operation = manager_1.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )


    manager_1.mark_failed(
        operation.operation_id
    )


    # ==================================
    # REINÍCIO
    # ==================================

    manager_2 = create_manager(
        db_path
    )


    restored = (
        manager_2.get_operation(
            operation.operation_id
        )
    )


    assert restored is None

    assert (
        manager_2.get_open_operations()
        == []
    )


    # A operação continua registrada
    # no histórico do SQLite.

    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )


    historical = repository.get(
        operation.operation_id
    )


    assert historical is not None

    assert (
        historical.status
        == "FAILED"
    )

def test_reconcile_operation_is_persisted(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )


    manager = create_manager(
        db_path
    )


    operation = manager.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )


    assert operation.status == "PENDING"


    manager.mark_reconcile(
        operation.operation_id
    )


    assert (
        operation.status
        == "RECONCILE"
    )


    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )


    loaded = repository.get(
        operation.operation_id
    )


    assert loaded is not None

    assert (
        loaded.status
        == "RECONCILE"
    )

    assert (
        loaded.max_stop_price
        == 183540.0
    )


def test_reconcile_operation_is_restored_as_active(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading_test.db"
    )


    # ==================================
    # PRIMEIRA EXECUÇÃO
    # ==================================

    manager_1 = create_manager(
        db_path
    )


    operation = manager_1.create_operation(
        broker_id="xp",
        feed="WIN",
        symbol="WINV26",
        side="BUY",
        volume=1.0,
        max_stop_price=183540.0,
    )


    manager_1.mark_reconcile(
        operation.operation_id
    )


    # ==================================
    # REINÍCIO
    # ==================================

    manager_2 = create_manager(
        db_path
    )


    restored = (
        manager_2.get_operation(
            operation.operation_id
        )
    )


    assert restored is not None

    assert (
        restored.status
        == "RECONCILE"
    )

    assert (
        restored.max_stop_price
        == 183540.0
    )


    active_operations = (
        manager_2.get_open_operations()
    )


    assert restored in active_operations

def test_find_open_operations_by_mt5_position_ticket(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading.db"
    )

    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )

    manager = OperationManager(
        repository=repository
    )


    operation_1 = (
        manager.create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1,
            max_stop_price=183955.0,
        )
    )

    operation_2 = (
        manager.create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1,
            max_stop_price=184000.0,
        )
    )


    manager.mark_open(
        operation_id=(
            operation_1.operation_id
        ),
        entry_price=184100.0,
        mt5_order_ticket=111111,
        mt5_position_ticket=999999,
    )

    manager.mark_open(
        operation_id=(
            operation_2.operation_id
        ),
        entry_price=184200.0,
        mt5_order_ticket=222222,
        mt5_position_ticket=999999,
    )


    found = (
        manager
        .find_open_by_mt5_position_ticket(
            mt5_position_ticket=999999
        )
    )


    assert len(found) == 2

    ids = {
        operation.operation_id
        for operation in found
    }

    assert ids == {
        operation_1.operation_id,
        operation_2.operation_id,
    }


    order_tickets = {
        operation.mt5_order_ticket
        for operation in found
    }

    assert order_tickets == {
        111111,
        222222,
    }


    assert all(
        operation.mt5_position_ticket
        == 999999
        for operation in found
    )

    assert all(
        operation.status == "OPEN"
        for operation in found
    )


def test_find_open_operations_by_mt5_position_ticket_returns_empty_list(
    tmp_path,
):

    db_path = (
        tmp_path
        / "trading.db"
    )

    repository = (
        TradingOperationRepository(
            db_path=str(db_path)
        )
    )

    manager = OperationManager(
        repository=repository
    )


    found = (
        manager
        .find_open_by_mt5_position_ticket(
            mt5_position_ticket=999999
        )
    )


    assert found == []