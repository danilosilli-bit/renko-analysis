import pandas as pd
from ingestion.mt5_client import MT5Client
from ingestion.tick_collector import TickCollector
import ingestion.tick_utils as tick_utils
import ingestion.tick_transformer as tick_transformer
import numpy as np
from IPython.display import display
import mplfinance as mpf
from matplotlib.patches import Rectangle
from storage.tick_repository import TickRepository
from storage.renko_repository import RenkoRepository
from storage.sqlite_manager import SQLiteManager
from renko.renko_engine import RenkoEngine


SYMBOL = "PETR4"
BRICK_SIZE = 10
START_DATE = pd.Timestamp("2026-06-12")
TICK_LIMIT = 1000



def main():
    client = MT5Client(login=50390846, server="XPMT5-DEMO")
    client.connect()

    ticks = TickCollector(client).collect_ticks_batch(
        SYMBOL,
        START_DATE,
        TICK_LIMIT
    )

    client.disconnect()

    new_ticks = tick_transformer.normalize_ticks(ticks)

    ticks_db = SQLiteManager("data/ticks.db")
    renko_db = SQLiteManager("data/renko.db")

    tick_repository = TickRepository(ticks_db)
    renko_repository = RenkoRepository(renko_db)

    tick_repository.create_table(SYMBOL)

    renko_repository.create_state_table()
    renko_repository.create_renko_table(SYMBOL)

    tick_repository.truncate_table(SYMBOL)

    tick_repository.save_ticks(
        SYMBOL,
        new_ticks
    )

    print("Ticks salvos:", tick_repository.count_ticks(SYMBOL))

    engine = RenkoEngine(
        SYMBOL,
        BRICK_SIZE,
        renko_repository
    )

    for tick in new_ticks:
        engine.process_tick(tick)

    renko_table_name = renko_repository.get_table_name(SYMBOL)

    closed_bricks = renko_db.execute(
        f"""
        SELECT COUNT(*) AS total
        FROM {renko_table_name}
        WHERE brick_size = ?
        """,
        (BRICK_SIZE,)
    )

    last_closed_brick = renko_repository.get_last_closed_brick(
        SYMBOL,
        BRICK_SIZE
    )

    final_state = renko_repository.get_state(
        SYMBOL,
        BRICK_SIZE
    )

    print("Bricks fechados:", closed_bricks[0]["total"] if closed_bricks else 0)

    _print_row("Último brick fechado:", last_closed_brick)
    _print_row("Renko state final:", final_state)

    df_renko = get_renko_plot_dataframe(
        renko_db,
        SYMBOL,
        BRICK_SIZE
    )
    df_plot = df_renko.copy()

    # garante colunas numéricas
    cols = ["Open", "High", "Low", "Close", "Volume"]
    df_plot[cols] = df_plot[cols].astype(float)

    # cria datas artificiais sequenciais para o Renko
    df_plot.index = pd.date_range(
        start="2026-01-01 09:00:00",
        periods=len(df_plot),
        freq="1min"
    )

    mpf.plot(
        df_plot,
        type="candle",
        style="charles",
        title="Renko PETR4",
        ylabel="Preço",
        figsize=(20, 8),
        volume=False
    )



def _print_row(label, row):
    print(label)
    if row is None:
        print("  None")
        return

    for key in row.keys():
        print(f"  {key}: {row[key]}")

def get_renko_plot_dataframe(db, symbol, brick_size):

    table_name = f"renko_{symbol.lower()}"

    rows = db.execute(
        f"""
        SELECT
            close_time,
            open,
            high,
            low,
            close,
            volume
        FROM {table_name}
        WHERE brick_size = ?
        ORDER BY id
        """,
        (brick_size,)
    )

    df = pd.DataFrame([dict(row) for row in rows])

    df["Date"] = pd.to_datetime(df["close_time"])

    df["Open"] = df["open"].astype(float)
    df["High"] = df["high"].astype(float)
    df["Low"] = df["low"].astype(float)
    df["Close"] = df["close"].astype(float)
    df["Volume"] = df["volume"].astype(float)

    df = df[
        ["Date", "Open", "High", "Low", "Close", "Volume"]
    ]

    df = df.set_index("Date")

    return df

if __name__ == "__main__":
    main()
