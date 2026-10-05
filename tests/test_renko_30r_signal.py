from trading.renko_30r_signal import (
    Renko30RSignal,
)


class FakeRenkoService:

    def __init__(self, bricks):
        self.bricks = bricks

    def get_bricks(
        self,
        brick_size: int,
    ):
        if brick_size != 30:
            return []

        return self.bricks


def test_buy_signal():

    bricks = [
        {
            "direction": "DOWN",
            "high": 184500.0,
            "low": 184350.0,
        },
        {
            "direction": "UP",
            "high": 184650.0,
            "low": 184500.0,
        },
    ]

    service = FakeRenkoService(
        bricks
    )

    signal = Renko30RSignal()

    result = signal.evaluate(
        service
    )

    assert result["ready"] is True
    assert result["direction"] == "BUY"

    assert result["can_buy"] is True
    assert result["can_sell"] is False

    assert (
        result["max_stop_price"]
        == 184330.0
    )

    assert (
        result["previous_brick"]["low"]
        == 184350.0
    )

    print("")
    print("BUY SIGNAL")
    print(result)


def test_sell_signal():

    bricks = [
        {
            "direction": "UP",
            "high": 184500.0,
            "low": 184350.0,
        },
        {
            "direction": "DOWN",
            "high": 184350.0,
            "low": 184200.0,
        },
    ]

    service = FakeRenkoService(
        bricks
    )

    signal = Renko30RSignal()

    result = signal.evaluate(
        service
    )

    assert result["ready"] is True
    assert result["direction"] == "SELL"

    assert result["can_buy"] is False
    assert result["can_sell"] is True

    assert (
        result["max_stop_price"]
        == 184520.0
    )

    assert (
        result["previous_brick"]["high"]
        == 184500.0
    )

    print("")
    print("SELL SIGNAL")
    print(result)


def test_not_ready():

    bricks = [
        {
            "direction": "UP",
            "high": 184500.0,
            "low": 184350.0,
        },
    ]

    service = FakeRenkoService(
        bricks
    )

    signal = Renko30RSignal()

    result = signal.evaluate(
        service
    )

    assert result["ready"] is False
    assert result["can_buy"] is False
    assert result["can_sell"] is False
    assert result["max_stop_price"] is None

    print("")
    print("NOT READY")
    print(result)
    