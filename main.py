from datetime import date, datetime, time

from ingestion.mt5_client import MT5Client
from ingestion.tick_collector import TickCollector
import ingestion.tick_transformer as tick_transformer

from storage.tick_repository import TickRepository
from storage.renko_repository import RenkoRepository
from storage.sqlite_manager import SQLiteManager

from renko.renko_engine import RenkoEngine
from market.instrument_config import InstrumentConfig


RUN_MODE = "renko_only"
# "collect_only"
# "renko_only"
# "collect_and_renko"

COLLECT_MODE = "day" 
# "batch"
# "day"

SYMBOLS = ["WINQ26"]

DATES = [
    date(2026, 6, 17), date(2026, 6, 18), date(2026, 6, 19), date(2026, 6, 22), date(2026, 6, 23)
]

TICK_LIMIT = 1000

MT5_LOGIN = 50390846
MT5_SERVER = "XPMT5-DEMO"


def collect_ticks(symbols, dates, collect_mode):
    client = MT5Client(
        login=MT5_LOGIN,
        server=MT5_SERVER
    )

    ticks_db = SQLiteManager("data/ticks.db")
    tick_repository = TickRepository(ticks_db)

    try:
        client.connect()
        collector = TickCollector(client)

        for symbol in symbols:
            tick_repository.create_table(symbol)

            for target_date in dates:
                print(f"Coletando ticks: {symbol} - {target_date}")

                if collect_mode == "batch":
                    start_datetime = datetime.combine(
                        target_date,
                        time.min
                    )

                    raw_ticks = collector.collect_ticks_batch(
                        symbol,
                        start_datetime,
                        TICK_LIMIT
                    )

                elif collect_mode == "day":
                    raw_ticks = collector.collect_ticks_day(
                        symbol,
                        target_date
                    )

                else:
                    raise ValueError(f"Collect mode inválido: {collect_mode}")

                if raw_ticks is None or len(raw_ticks) == 0:
                    print(f"Nenhum tick encontrado para {symbol} em {target_date}")
                    continue

                normalized_ticks = tick_transformer.normalize_ticks(raw_ticks)

                tick_repository.save_ticks(
                    symbol,
                    normalized_ticks
                )

                print(f"Ticks salvos: {symbol} - {len(normalized_ticks)}")

    finally:
        client.disconnect()


def process_renko(symbols):
    ticks_db = SQLiteManager("data/ticks.db")
    renko_db = SQLiteManager("data/renko.db")

    tick_repository = TickRepository(ticks_db)
    renko_repository = RenkoRepository(renko_db)

    renko_repository.create_state_table()

    for symbol in symbols:
        instrument = InstrumentConfig.from_symbol(symbol)

        renko_repository.create_renko_table(symbol)

        for target_date in DATES:
            print(f"Processando dia: {symbol} - {target_date}")

            ticks = tick_repository.get_ticks_by_day(
                symbol,
                target_date
            )

            if ticks is None or len(ticks) == 0:
                print(f"Nenhum tick salvo para {symbol} em {target_date}")
                continue

            for brick_size in instrument.renko_sizes:
                print(f"Processando Renko: {symbol} - {brick_size} - {target_date}")

                engine = RenkoEngine(
                    symbol=symbol,
                    brick_size=brick_size,
                    renko_repository=renko_repository,
                    persist_state_every_tick=False
                )

                for tick in ticks:
                    engine.process_tick(tick)

                engine.flush_state()

                last_brick = renko_repository.get_last_closed_brick(
                    symbol,
                    brick_size
                )

                print("Último brick:", dict(last_brick) if last_brick else None)


def main():
    if RUN_MODE == "collect_only":
        collect_ticks(
            SYMBOLS,
            DATES,
            COLLECT_MODE
        )

    elif RUN_MODE == "renko_only":
        process_renko(SYMBOLS)

    elif RUN_MODE == "collect_and_renko":
        collect_ticks(
            SYMBOLS,
            DATES,
            COLLECT_MODE
        )

        process_renko(SYMBOLS)

    else:
        raise ValueError(f"RUN_MODE inválido: {RUN_MODE}")


if __name__ == "__main__":
    main()