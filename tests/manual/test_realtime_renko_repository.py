from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from storage.sqlite_manager import SQLiteManager
from storage.renko_repository import RenkoRepository
from storage.intraday_repository import IntradayRepository
from storage.realtime_renko_repository import (
    RealtimeRenkoRepository,
)


HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"
BRICK_SIZE = 10


def main():

    historical_db = SQLiteManager(
        str(HISTORICAL_RENKO_DB)
    )

    historical_repository = RenkoRepository(
        historical_db
    )

    intraday = IntradayRepository()

    intraday.prepare_symbol(
        INTRADAY_SYMBOL
    )

    repository = RealtimeRenkoRepository(
        historical_repository=historical_repository,
        intraday_repository=intraday.renko_repository,
        historical_symbol=HISTORICAL_SYMBOL,
        intraday_symbol=INTRADAY_SYMBOL,
    )

    print()
    print("LEITURA DO HISTÓRICO")
    print("==============================")

    state = repository.get_state(
        "IGNORED",
        BRICK_SIZE,
    )

    last_brick = repository.get_last_closed_brick(
        "IGNORED",
        BRICK_SIZE,
    )

    print(
        f"state encontrado      : {state is not None}"
    )

    print(
        f"last brick encontrado : {last_brick is not None}"
    )

    if state is not None:
        print(
            f"state symbol          : {state['symbol']}"
        )
        print(
            f"state open            : {state['open']}"
        )
        print(
            f"state last            : {state['last']}"
        )

    if last_brick is not None:
        print(
            f"last brick close      : {last_brick['close']}"
        )
        print(
            f"last brick direction  : {last_brick['direction']}"
        )

    print()
    print("GRAVAÇÃO INTRADAY")
    print("==============================")

    test_brick = {
        "brick_size": 10,
        "open_time": 1789221000000,
        "close_time": 1789221001000,

        "open": 188685.0,
        "close": 188730.0,

        "high": 188730.0,
        "low": 188685.0,

        "direction": "UP",

        "volume": 0,

        "buy_qty": 0.0,
        "sell_qty": 0.0,

        "buy_financial": 0.0,
        "sell_financial": 0.0,

        "trades_count": 0,
    }

    repository.save_brick(
        "IGNORED",
        test_brick,
    )

    table_name = (
        intraday
        .renko_repository
        .get_table_name(
            INTRADAY_SYMBOL
        )
    )

    rows = intraday.renko_db.execute(
        f"""
        SELECT *
        FROM {table_name}
        ORDER BY id DESC
        LIMIT 1
        """
    )

    print(
        f"bricks intraday encontrados : {len(rows)}"
    )

    if rows:
        row = rows[0]

        print(
            f"brick_size   : {row['brick_size']}"
        )
        print(
            f"open         : {row['open']}"
        )
        print(
            f"close        : {row['close']}"
        )
        print(
            f"direction    : {row['direction']}"
        )

    print()
    print("STATE INTRADAY")
    print("==============================")

    tables = intraday.renko_db.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    )

    table_names = [
        row["name"]
        for row in tables
    ]

    print(
        f"renko_state existe : "
        f"{'renko_state' in table_names}"
    )


if __name__ == "__main__":
    main()