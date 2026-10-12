from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from storage.sqlite_manager import SQLiteManager
from storage.renko_repository import RenkoRepository
from renko.renko_engine import RenkoEngine


SYMBOL = "WINV26"

BRICK_SIZES = (
    10,
    30,
    45,
)


def main():

    db = SQLiteManager(
        str(HISTORICAL_RENKO_DB)
    )

    repository = RenkoRepository(
        db
    )

    print()
    print("HISTORICAL RENKO BOOTSTRAP")
    print("==============================")
    print(f"DB: {HISTORICAL_RENKO_DB}")
    print(f"Símbolo: {SYMBOL}")

    for brick_size in BRICK_SIZES:

        engine = RenkoEngine(
            symbol=SYMBOL,
            brick_size=brick_size,
            renko_repository=repository,
            persist_state_every_tick=False,
        )

        # Apenas força o RenkoEngine a recuperar:
        #
        # 1. renko_state
        # 2. último brick fechado
        #
        # Se existir saved_state, este tick
        # não será usado para criar estado novo.
        dummy_tick = {
            "timestamp_ms": 0,
            "last": 0.0,
            "volume": 0.0,
            "buy_qty": 0.0,
            "sell_qty": 0.0,
            "buy_financial": 0.0,
            "sell_financial": 0.0,
        }

        engine._initialize_state(
            dummy_tick
        )

        print()
        print(
            f"{brick_size}R"
        )
        print("------------------------------")

        state = engine.state
        brick = engine.last_closed_brick

        if state is None:
            print("STATE: NÃO ENCONTRADO")
        else:
            print("STATE")
            print(
                f"  open_time    : {state.open_time}"
            )
            print(
                f"  open         : {state.open}"
            )
            print(
                f"  last         : {state.last}"
            )
            print(
                f"  high         : {state.high}"
            )
            print(
                f"  low          : {state.low}"
            )
            print(
                f"  volume       : {state.volume}"
            )
            print(
                f"  trades_count : {state.trades_count}"
            )

        if brick is None:
            print(
                "LAST BRICK: NÃO ENCONTRADO"
            )
        else:
            print("LAST BRICK")
            print(
                f"  open_time  : "
                f"{brick['open_time']}"
            )
            print(
                f"  close_time : "
                f"{brick['close_time']}"
            )
            print(
                f"  open        : "
                f"{brick['open']}"
            )
            print(
                f"  close       : "
                f"{brick['close']}"
            )
            print(
                f"  high        : "
                f"{brick['high']}"
            )
            print(
                f"  low         : "
                f"{brick['low']}"
            )
            print(
                f"  direction   : "
                f"{brick['direction']}"
            )


if __name__ == "__main__":
    main()