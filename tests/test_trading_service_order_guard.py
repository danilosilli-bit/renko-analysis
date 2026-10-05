from trading.broker_router import BrokerRouter
from trading.trading_service import TradingService
from trading.order_guard import OrderGuard


class FakeFeedService:

    def __init__(self):
        self.running = True
        self.send_market_order_called = False

    def send_market_order(
        self,
        side,
        volume,
        check_only,
        feed,
    ):
        self.send_market_order_called = True

        return "fake-request-id"

    def wait_for_command_result(
        self,
        request_id,
        timeout,
    ):
        return {
            "result": {
                "retcode": 0,
            }
        }


def create_router(
    feed_service,
):

    router = BrokerRouter()

    router.register(
        broker_id="xp",
        feed_service=feed_service,
        feed="WIN",
        symbol="WINV26",
    )

    return router


def test_blocked_order_never_reaches_feed():

    feed_service = FakeFeedService()

    router = create_router(
        feed_service
    )

    def signal_provider(feed):

        return {
            "ready": True,
            "direction": "SELL",
            "can_buy": False,
            "can_sell": True,
            "max_stop_price": 184315.0,
        }

    guard = OrderGuard(
        signal_provider
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=guard,
    )

    result = service.send_market_order(
        side="BUY",
        volume=1,
        check_only=False,
    )

    assert result["status"] == "BLOCKED"

    assert (
        feed_service
        .send_market_order_called
        is False
    )


def test_allowed_order_reaches_feed():

    feed_service = FakeFeedService()

    router = create_router(
        feed_service
    )

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

    service = TradingService(
        broker_router=router,
        broker_id="xp",
        order_guard=guard,
    )

    result = service.send_market_order(
        side="BUY",
        volume=1,
        check_only=True,
    )

    assert result["status"] == "OK"

    assert (
        feed_service
        .send_market_order_called
        is True
    )

    assert (
        result["guard"]
        ["max_stop_price"]
        == 183955.0
    )

def test_missing_guard_blocks_order():

    feed_service = FakeFeedService()

    router = create_router(
        feed_service
    )

    service = TradingService(
        broker_router=router,
        broker_id="xp",
    )

    result = service.send_market_order(
        side="BUY",
        volume=1,
        check_only=False,
    )

    assert result["status"] == "BLOCKED"

    assert (
        feed_service
        .send_market_order_called
        is False
    )
    