import sqlite3
from pathlib import Path


class RenkoDatabaseBootstrap:

    def __init__(self, db_path="data/renko.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.db_path)

    def get_table_name(self, symbol):
        symbol = symbol.lower().replace("@", "").replace("$", "")
        return f"renko_{symbol}"

    def create_renko_table(self, symbol):
        table_name = self.get_table_name(symbol)

        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            brick_size REAL,

            open_time TEXT,
            close_time TEXT,

            open REAL,
            close REAL,

            high REAL,
            low REAL,

            direction TEXT,

            volume REAL,

            buy_qty REAL,
            sell_qty REAL,

            buy_financial REAL,
            sell_financial REAL,

            trades_count INTEGER
        )
        """

        self.db.execute(query)
        self.db.commit()

        return table_name

    def insert_first_renko(self, symbol, brick):
        table_name = self.get_table_name(symbol)

        query = f"""
        INSERT INTO {table_name} (
            brick_size,
            open_time,
            close_time,
            open,
            close,
            high,
            low,
            direction,
            volume,
            buy_qty,
            sell_qty,
            buy_financial,
            sell_financial,
            trades_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            brick["brick_size"],
            brick["open_time"],
            brick["close_time"],
            brick["open"],
            brick["close"],
            brick["high"],
            brick["low"],
            brick["direction"],
            brick["volume"],
            brick["buy_qty"],
            brick["sell_qty"],
            brick["buy_financial"],
            brick["sell_financial"],
            brick["trades_count"],
        )

        self.db.execute(query, values)
        self.db.commit()

    def close(self):
        self.db.close()


def main():
    symbol = "PETR4"

    first_brick = {
        "brick_size": 7,
        "open_time": "2026-06-11 17:30:00",
        "close_time": "2026-06-11 17:30:48",
        "open": 41.64,
        "close": 41.58,
        "high": 41.75,
        "low": 41.58,
        "direction": "DOWN",
        "volume": 34600,
        "buy_qty": 0,
        "sell_qty": 0,
        "buy_financial": 0,
        "sell_financial": 0,
        "trades_count": 77,
    }

    bootstrap = RenkoDatabaseBootstrap()

    try:
        #table_name = bootstrap.create_renko_table(symbol)
        bootstrap.insert_first_renko(symbol, first_brick)

        #print(f"Tabela criada/verificada: {table_name}")
        print("Primeiro Renko inserido com sucesso.")

    finally:
        bootstrap.close()


if __name__ == "__main__":
    main()


