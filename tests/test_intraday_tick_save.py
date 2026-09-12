from market.intraday_tick import IntradayTick
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

    repository.tick_repository.save_tick(
        SYMBOL,
        tick
    )

    count = repository.tick_repository.count_ticks(
        SYMBOL
    )

    rows = repository.tick_repository.get_all_ticks(
        SYMBOL
    )

    print()
    print("Ticks salvos:", count)

    print()
    print("Conteúdo:")
    for row in rows:
        print(dict(row))


if __name__ == "__main__":
    main()