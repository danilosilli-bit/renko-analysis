from market.realtime_tick import RealtimeTick
from services.intraday_tick_adapter import realtime_to_intraday_tick
from storage.intraday_repository import IntradayRepository


SYMBOL = "Bra50Oct26"


def main():
    repository = IntradayRepository()

    repository.prepare_symbol(
        SYMBOL
    )

    repository.tick_repository.truncate_table(
        SYMBOL
    )

    realtime_tick = RealtimeTick(
        symbol=SYMBOL,
        timestamp_ms=1789220000000,

        price=188000.0,

        bid=188000.0,
        ask=188025.0,
        spread=25.0,

        last=0.0,

        source_price="bid",
    )

    intraday_tick = realtime_to_intraday_tick(
        realtime_tick
    )

    print()
    print("REALTIME TICK")
    print("========================")
    print(realtime_tick)

    print()
    print("INTRADAY TICK")
    print("========================")
    print(intraday_tick)

    repository.tick_repository.save_tick(
        SYMBOL,
        intraday_tick
    )

    rows = repository.tick_repository.get_all_ticks(
        SYMBOL
    )

    print()
    print("SALVO NO BANCO")
    print("========================")

    for row in rows:
        print(dict(row))


if __name__ == "__main__":
    main()
    