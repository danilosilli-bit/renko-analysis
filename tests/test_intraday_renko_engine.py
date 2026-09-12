from market.intraday_tick import IntradayTick

from services.intraday_renko_adapter import (
    intraday_to_renko_tick,
)

from renko.renko_engine import RenkoEngine

from services.renko_service import (
    InMemoryRenkoRepository,
)


SYMBOL = "Bra50"
BRICK_SIZE = 10


def make_tick(
    timestamp_ms: int,
    price: float,
):
    return IntradayTick(
        timestamp_ms=timestamp_ms,

        price=price,

        bid=price,
        ask=price + 25,
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


def main():

    repository = InMemoryRenkoRepository()

    engine = RenkoEngine(
        symbol=SYMBOL,
        brick_size=BRICK_SIZE,
        renko_repository=repository,
        persist_state_every_tick=False,
    )

    ticks = [
        make_tick(
            1789220000000,
            188000.0,
        ),
        make_tick(
            1789220001000,
            188020.0,
        ),
        make_tick(
            1789220002000,
            188045.0,
        ),
        make_tick(
            1789220003000,
            188090.0,
        ),
        make_tick(
            1789220004000,
            188135.0,
        ),
    ]

    print()
    print("PROCESSANDO TICKS")
    print("========================")

    for intraday_tick in ticks:

        renko_tick = intraday_to_renko_tick(
            intraday_tick
        )

        print(
            f"price={intraday_tick.price:.0f}"
        )

        engine.process_tick(
            renko_tick
        )

    print()
    print("ESTADO FINAL")
    print("========================")
    print(engine.state)

    print()
    print("ÚLTIMO BRICK")
    print("========================")
    print(engine.last_closed_brick)


if __name__ == "__main__":
    main()