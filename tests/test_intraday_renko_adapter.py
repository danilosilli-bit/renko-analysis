from market.intraday_tick import IntradayTick

from services.intraday_renko_adapter import (
    intraday_to_renko_tick,
)


def main():

    tick = IntradayTick(
        timestamp_ms=1789220000000,

        price=188000.0,

        bid=188000.0,
        ask=188025.0,
        last=0.0,
        spread=25.0,

        volume=None,
        volume_real=None,
        flags=None,
        is_auction=None,

        buy_qty=None,
        sell_qty=None,

        buy_financial=None,
        sell_financial=None,

        source_type="CFD",
        source_symbol="Bra50Oct26",
        price_source="bid",
    )

    renko_tick = intraday_to_renko_tick(
        tick
    )

    print()
    print("INTRADAY TICK")
    print("========================")
    print(tick)

    print()
    print("RENKO TICK")
    print("========================")

    for key, value in renko_tick.items():
        print(
            f"{key:20} {value}"
        )


if __name__ == "__main__":
    main()