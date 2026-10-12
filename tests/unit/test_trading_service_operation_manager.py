from trading.broker_router import (
    BrokerRouter,
)

from trading.operation_manager import (
    OperationManager,
)

from trading.trading_service import (
    TradingService,
)


class FakeFeedService:

    def __init__(self):
        self.running = True
        self.calls = []

    def send_market_order(
        self,
        feed,
        side,
        volume,
        check_only,
    ):
        self.calls.append(
            {
                "feed": feed,
                "side": side,
                "volume": volume,
                "check_only": check_only,
            }
        )

        return "request-1"

    def wait_for_command_result(
        self,
        request_id,
        timeout,
    ):
        return {
            "result": {
                "success": True,
                "stage": "check_only",
            }
        }


class FakeOrderGuard:

    def validate_entry(
        self,
        feed,
        side,
    ):
        return {
            "allowed": True,
            "feed": feed,
            "side": side,
            "direction": side,
            "max_stop_price": 183540.0,
        }


def test_check_only_does_not_create_operation():

    feed_service = FakeFeedService()

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    operation_manager = (
        OperationManager()
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    result = service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=True,
        broker_id="xp",
    )

    assert result["status"] == "OK"

    assert len(
        feed_service.calls
    ) == 1

    assert (
        feed_service.calls[0][
            "check_only"
        ]
        is True
    )

    assert (
        result["result"]["success"]
        is True
    )

    assert (
        result["result"]["stage"]
        == "check_only"
    )

    assert (
        operation_manager
        .get_operations()
        == []
    )

def test_real_order_creates_pending_before_feed_send():

    operation_manager = (
        OperationManager()
    )

    class PendingAwareFeedService:

        def __init__(self):
            self.running = True
            self.pending_seen_before_send = False

        def send_market_order(
            self,
            feed,
            side,
            volume,
            check_only,
        ):
            active_operations = (
                operation_manager
                .get_open_operations()
            )

            self.pending_seen_before_send = (
                len(active_operations) == 1
                and active_operations[0].status
                == "PENDING"
            )

            return "request-real-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": True,
                    "stage": "send",
                    "result": {
                        "retcode": 10009,
                        "deal": 123456,
                        "order": 654321,
                        "volume": 1.0,
                        "price": 183600.0,
                    },
                    "position_ticket": 777777,
                }
            }

    feed_service = (
        PendingAwareFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=False,
        broker_id="xp",
    )

    assert (
        feed_service
        .pending_seen_before_send
        is True
    )

    operations = (
        operation_manager
        .get_operations()
    )

    assert len(operations) == 1

    assert (
        operations[0].status
        == "OPEN"
    )

    assert (
        operations[0].max_stop_price
        == 183540.0
    )

def test_real_order_timeout_marks_operation_reconcile():

    operation_manager = (
        OperationManager()
    )

    class TimeoutFeedService:

        def __init__(self):
            self.running = True

        def send_market_order(
            self,
            feed,
            side,
            volume,
            check_only,
        ):
            return "request-timeout-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return None

    feed_service = (
        TimeoutFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    result = service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=False,
        broker_id="xp",
    )

    assert (
        result["status"]
        == "TIMEOUT"
    )

    operations = (
        operation_manager
        .get_operations()
    )

    assert len(operations) == 1

    operation = operations[0]

    assert (
        operation.status
        == "RECONCILE"
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )

def test_real_order_worker_error_marks_operation_reconcile():

    operation_manager = (
        OperationManager()
    )

    class ErrorFeedService:

        def __init__(self):
            self.running = True

        def send_market_order(
            self,
            feed,
            side,
            volume,
            check_only,
        ):
            return "request-error-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "error":
                    "Erro simulado no worker."
            }

    feed_service = (
        ErrorFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    result = service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=False,
        broker_id="xp",
    )

    assert (
        result["status"]
        == "ERROR"
    )

    operations = (
        operation_manager
        .get_operations()
    )

    assert len(operations) == 1

    operation = operations[0]

    assert (
        operation.status
        == "RECONCILE"
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )

def test_real_order_check_rejection_marks_operation_failed():

    operation_manager = (
        OperationManager()
    )

    class RejectedFeedService:

        def __init__(self):
            self.running = True

        def send_market_order(
            self,
            feed,
            side,
            volume,
            check_only,
        ):
            return "request-rejected-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": False,
                    "stage": "check",
                    "check": {
                        "retcode": 10030,
                    },
                }
            }

    feed_service = (
        RejectedFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    result = service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=False,
        broker_id="xp",
    )

    operations = (
        operation_manager
        .get_operations()
    )

    assert len(operations) == 1

    operation = operations[0]

    assert (
        operation.status
        == "FAILED"
    )

    assert (
        operation.mt5_order_ticket
        is None
    )

    assert (
        operation.mt5_position_ticket
        is None
    )

    assert (
        operation.entry_price
        is None
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )

    assert (
        result["result"]["success"]
        is False
    )

    assert (
        result["result"]["stage"]
        == "check"
    )

def test_real_order_confirmed_execution_marks_operation_open():

    operation_manager = (
        OperationManager()
    )

    class ExecutedFeedService:

        def __init__(self):
            self.running = True

        def send_market_order(
            self,
            feed,
            side,
            volume,
            check_only,
        ):
            return "request-executed-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": True,
                    "stage": "send",
                    "result": {
                        "retcode": 10009,
                        "deal": 123456,
                        "order": 654321,
                        "volume": 1.0,
                        "price": 183600.0,
                    },
                    "position_ticket": 777777,
                }
            }

    feed_service = (
        ExecutedFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    result = service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=False,
        broker_id="xp",
    )

    operations = (
        operation_manager
        .get_operations()
    )

    assert len(operations) == 1

    operation = operations[0]

    assert (
        operation.status
        == "OPEN"
    )

    assert (
        operation.entry_price
        == 183600.0
    )

    assert (
        operation.mt5_order_ticket
        == 654321
    )

    assert (
        operation.mt5_position_ticket
        == 777777
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )

    assert (
        operation.current_stop_price
        == 183540.0
    )

    assert (
        result["result"]["success"]
        is True
    )

    assert (
        result["result"]["stage"]
        == "send"
    )

def test_real_order_success_without_ticket_marks_reconcile():

    operation_manager = (
        OperationManager()
    )

    class MissingTicketFeedService:

        def __init__(self):
            self.running = True

        def send_market_order(
            self,
            feed,
            side,
            volume,
            check_only,
        ):
            return "request-missing-ticket-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": True,
                    "stage": "send",
                    "result": {
                        "retcode": 10009,
                        "deal": 123456,
                        "order": 0,
                        "volume": 1.0,
                        "price": 183600.0,
                    },
                }
            }

    feed_service = (
        MissingTicketFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=False,
        broker_id="xp",
    )

    operations = (
        operation_manager
        .get_operations()
    )

    assert len(operations) == 1

    operation = operations[0]

    assert (
        operation.status
        == "RECONCILE"
    )

    assert (
        operation.mt5_order_ticket
        is None
    )

    assert (
        operation.mt5_position_ticket
        is None
    )

    assert (
        operation.entry_price
        is None
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )

def test_real_order_success_without_position_ticket_marks_reconcile():

    operation_manager = (
        OperationManager()
    )

    class MissingPositionTicketFeedService:

        def __init__(self):
            self.running = True

        def send_market_order(
            self,
            feed,
            side,
            volume,
            check_only,
        ):
            return (
                "request-missing-position-ticket-1"
            )

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": True,
                    "stage": "send",
                    "result": {
                        "retcode": 10009,
                        "deal": 123456,
                        "order": 654321,
                        "volume": 1.0,
                        "price": 183600.0,
                    },
                    "position_ticket": None,
                    "position_ticket_error": (
                        "Falha simulada ao resolver "
                        "position_id."
                    ),
                }
            }

    feed_service = (
        MissingPositionTicketFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=False,
        broker_id="xp",
    )

    operations = (
        operation_manager
        .get_operations()
    )

    assert len(operations) == 1

    operation = operations[0]

    assert (
        operation.status
        == "RECONCILE"
    )

    assert (
        operation.mt5_order_ticket
        is None
    )

    assert (
        operation.mt5_position_ticket
        is None
    )

    assert (
        operation.entry_price
        is None
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )

def test_real_order_send_failure_marks_reconcile():

    operation_manager = (
        OperationManager()
    )

    class SendFailureFeedService:

        def __init__(self):
            self.running = True

        def send_market_order(
            self,
            feed,
            side,
            volume,
            check_only,
        ):
            return "request-send-failure-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": False,
                    "stage": "send",
                    "result": {
                        "retcode": 10021,
                        "deal": 0,
                        "order": 0,
                        "volume": 0.0,
                        "price": 0.0,
                    },
                }
            }

    feed_service = (
        SendFailureFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )

    result = service.send_market_order(
        side="BUY",
        volume=1.0,
        check_only=False,
        broker_id="xp",
    )

    operations = (
        operation_manager
        .get_operations()
    )

    assert len(operations) == 1

    operation = operations[0]

    assert (
        operation.status
        == "RECONCILE"
    )

    assert (
        operation.mt5_order_ticket
        is None
    )

    assert (
        operation.mt5_position_ticket
        is None
    )

    assert (
        operation.entry_price
        is None
    )

    assert (
        operation.max_stop_price
        == 183540.0
    )

    assert (
        result["result"]["success"]
        is False
    )

    assert (
        result["result"]["stage"]
        == "send"
    )

def test_confirmed_close_marks_operation_closed():

    operation_manager = (
        OperationManager()
    )

    operation = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=654321,
        mt5_position_ticket=777777,
    )


    class CloseFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-close-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": True,
                    "stage": "send",
                    "result": {
                        "retcode": 10009,
                        "deal": 987654,
                        "order": 654322,
                        "volume": 1.0,
                        "price": 183700.0,
                    },
                }
            }


    feed_service = CloseFeedService()

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id=(
            operation.operation_id
        ),
        check_only=False,
        expected_feed="WIN",
    )


    assert result["status"] == "OK"

    assert (
        operation.status
        == "CLOSED"
    )


    assert len(
        feed_service.close_calls
    ) == 1

    close_call = (
        feed_service.close_calls[0]
    )

    assert (
        close_call["ticket"]
        == 777777
    )

    assert (
        close_call["volume"]
        == 1.0
    )

    assert (
        close_call["feed"]
        == "WIN"
    )

    assert (
        close_call["check_only"]
        is False
    )
def test_close_check_only_does_not_mark_operation_closed():

    operation_manager = (
        OperationManager()
    )

    operation = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=654321,
        mt5_position_ticket=777777,
    )


    class CloseCheckOnlyFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-close-check-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": True,
                    "stage": "check_only",
                }
            }


    feed_service = (
        CloseCheckOnlyFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id=(
            operation.operation_id
        ),
        check_only=True,
        expected_feed="WIN",
    )


    assert result["status"] == "OK"

    assert (
        operation.status
        == "OPEN"
    )


    assert len(
        feed_service.close_calls
    ) == 1

    close_call = (
        feed_service.close_calls[0]
    )

    assert (
        close_call["ticket"]
        == 777777
    )

    assert (
        close_call["volume"]
        == 1.0
    )

    assert (
        close_call["check_only"]
        is True
    )

    assert (
        close_call["feed"]
        == "WIN"
    )

def test_rejected_close_does_not_mark_operation_closed():

    operation_manager = (
        OperationManager()
    )

    operation = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=654321,
        mt5_position_ticket=777777,
    )


    class RejectedCloseFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-close-rejected-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": False,
                    "stage": "send",
                    "result": {
                        "retcode": 10021,
                        "deal": 0,
                        "order": 0,
                        "volume": 0.0,
                        "price": 0.0,
                    },
                }
            }


    feed_service = (
        RejectedCloseFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id=(
            operation.operation_id
        ),
        check_only=False,
        expected_feed="WIN",
    )


    assert result["status"] == "OK"

    assert (
        result["result"]["success"]
        is False
    )

    assert (
        operation.status
        == "OPEN"
    )


    assert len(
        feed_service.close_calls
    ) == 1

    close_call = (
        feed_service.close_calls[0]
    )

    assert (
        close_call["ticket"]
        == 777777
    )

    assert (
        close_call["volume"]
        == 1.0
    )

    assert (
        close_call["check_only"]
        is False
    )

    assert (
        close_call["feed"]
        == "WIN"
    )

def test_close_timeout_marks_operation_reconcile():

    operation_manager = (
        OperationManager()
    )

    operation = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=654321,
        mt5_position_ticket=777777,
    )


    class CloseTimeoutFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-close-timeout-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return None


    feed_service = (
        CloseTimeoutFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id=(
            operation.operation_id
        ),
        check_only=False,
        expected_feed="WIN",
    )


    assert (
        result["status"]
        == "TIMEOUT"
    )

    assert (
        operation.status
        == "RECONCILE"
    )


    assert len(
        feed_service.close_calls
    ) == 1

    close_call = (
        feed_service.close_calls[0]
    )

    assert (
        close_call["ticket"]
        == 777777
    )

    assert (
        close_call["volume"]
        == 1.0
    )

    assert (
        close_call["check_only"]
        is False
    )

    assert (
        close_call["feed"]
        == "WIN"
    )

def test_close_worker_error_marks_operation_reconcile():

    operation_manager = (
        OperationManager()
    )

    operation = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=654321,
        mt5_position_ticket=777777,
    )


    class CloseErrorFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-close-error-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "error":
                    "Erro simulado no worker."
            }


    feed_service = (
        CloseErrorFeedService()
    )

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id=(
            operation.operation_id
        ),
        check_only=False,
        expected_feed="WIN",
    )


    assert (
        result["status"]
        == "ERROR"
    )

    assert (
        operation.status
        == "RECONCILE"
    )


    assert len(
        feed_service.close_calls
    ) == 1

    close_call = (
        feed_service.close_calls[0]
    )

    assert (
        close_call["ticket"]
        == 777777
    )

    assert (
        close_call["volume"]
        == 1.0
    )

    assert (
        close_call["check_only"]
        is False
    )

    assert (
        close_call["feed"]
        == "WIN"
    )

def test_confirmed_close_marks_only_matching_operation_closed():

    operation_manager = (
        OperationManager()
    )

    operation_1 = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation_1.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=111111,
        mt5_position_ticket=999999,
    )

    operation_2 = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183570.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation_2.operation_id
        ),
        entry_price=183650.0,
        mt5_order_ticket=222222,
        mt5_position_ticket=999999,
    )


    class CloseFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-close-multiple-1"

        def wait_for_command_result(
            self,
            request_id,
            timeout,
        ):
            return {
                "result": {
                    "success": True,
                    "stage": "send",
                    "result": {
                        "retcode": 10009,
                        "deal": 987654,
                        "order": 333333,
                        "volume": 1.0,
                        "price": 183700.0,
                    },
                }
            }


    feed_service = CloseFeedService()

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id=(
            operation_1.operation_id
        ),
        check_only=False,
        expected_feed="WIN",
    )


    assert result["status"] == "OK"

    assert (
        operation_1.status
        == "CLOSED"
    )

    assert (
        operation_2.status
        == "OPEN"
    )


    assert len(
        feed_service.close_calls
    ) == 1

    close_call = (
        feed_service.close_calls[0]
    )

    assert (
        close_call["ticket"]
        == 999999
    )

    assert (
        close_call["volume"]
        == 1.0
    )

    assert (
        close_call["feed"]
        == "WIN"
    )

    assert (
        close_call["check_only"]
        is False
    )

def test_close_rejects_operation_from_wrong_feed():

    operation_manager = (
        OperationManager()
    )

    operation = (
        operation_manager
        .create_operation(
            broker_id="activtrades",
            feed="CFD",
            symbol="Bra50Oct26",
            side="BUY",
            volume=0.05,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=654321,
        mt5_position_ticket=777777,
    )


    class CloseFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-should-not-happen"


    feed_service = CloseFeedService()

    router = BrokerRouter()

    router.register(
        broker_id="activtrades",
        feed_service=feed_service,
        feed="CFD",
        symbol="Bra50Oct26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="activtrades",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id=(
            operation.operation_id
        ),
        check_only=False,
        expected_feed="WIN",
    )


    assert (
        result["status"]
        == "ERROR"
    )

    assert (
        operation.status
        == "OPEN"
    )

    assert (
        feed_service.close_calls
        == []
    )

def test_close_rejects_operation_without_position_ticket():

    operation_manager = (
        OperationManager()
    )

    operation = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            operation.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=654321,
        mt5_position_ticket=None,
    )


    class CloseFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-should-not-happen"


    feed_service = CloseFeedService()

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id=(
            operation.operation_id
        ),
        check_only=False,
        expected_feed="WIN",
    )


    assert (
        result["status"]
        == "ERROR"
    )

    assert (
        operation.status
        == "OPEN"
    )

    assert (
        feed_service.close_calls
        == []
    ) 

def test_close_rejects_unknown_operation_id():

    operation_manager = (
        OperationManager()
    )


    class CloseFeedService:

        def __init__(self):
            self.running = True
            self.close_calls = []

        def close_position(
            self,
            ticket,
            volume,
            check_only,
            feed,
        ):
            self.close_calls.append(
                {
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "feed": feed,
                }
            )

            return "request-should-not-happen"


    feed_service = CloseFeedService()

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    result = service.close_position(
        operation_id="operation-does-not-exist",
        check_only=False,
        expected_feed="WIN",
    )


    assert (
        result["status"]
        == "ERROR"
    )

    assert (
        feed_service.close_calls
        == []
    )

def test_get_open_operations_filters_by_feed():

    operation_manager = (
        OperationManager()
    )


    win_operation = (
        operation_manager
        .create_operation(
            broker_id="xp",
            feed="WIN",
            symbol="WINV26",
            side="BUY",
            volume=1.0,
            max_stop_price=183540.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            win_operation.operation_id
        ),
        entry_price=183600.0,
        mt5_order_ticket=111111,
        mt5_position_ticket=999999,
    )


    cfd_operation = (
        operation_manager
        .create_operation(
            broker_id="activtrades",
            feed="CFD",
            symbol="Bra50Oct26",
            side="SELL",
            volume=0.05,
            max_stop_price=183700.0,
        )
    )

    operation_manager.mark_open(
        operation_id=(
            cfd_operation.operation_id
        ),
        entry_price=183650.0,
        mt5_order_ticket=222222,
        mt5_position_ticket=888888,
    )


    router = BrokerRouter()

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=FakeOrderGuard(),
        operation_manager=operation_manager,
    )


    win_result = (
        service.get_open_operations(
            expected_feed="WIN"
        )
    )

    cfd_result = (
        service.get_open_operations(
            expected_feed="CFD"
        )
    )


    assert (
        win_result["status"]
        == "OK"
    )

    assert (
        cfd_result["status"]
        == "OK"
    )


    assert len(
        win_result["operations"]
    ) == 1

    assert len(
        cfd_result["operations"]
    ) == 1


    win_item = (
        win_result["operations"][0]
    )

    cfd_item = (
        cfd_result["operations"][0]
    )


    assert (
        win_item["operation_id"]
        == win_operation.operation_id
    )

    assert (
        win_item["feed"]
        == "WIN"
    )

    assert (
        win_item["mt5_order_ticket"]
        == 111111
    )

    assert (
        win_item["mt5_position_ticket"]
        == 999999
    )


    assert (
        cfd_item["operation_id"]
        == cfd_operation.operation_id
    )

    assert (
        cfd_item["feed"]
        == "CFD"
    )

    assert (
        cfd_item["mt5_order_ticket"]
        == 222222
    )

    assert (
        cfd_item["mt5_position_ticket"]
        == 888888
    )