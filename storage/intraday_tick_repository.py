from datetime import datetime, timezone

from market.intraday_tick import IntradayTick


class IntradayTickRepository:

    def __init__(self, db_manager):
        self.db = db_manager

    def get_table_name(self, symbol):
        return f"ticks_{symbol.lower()}"

    def create_table(self, symbol):
        table_name = self.get_table_name(symbol)

        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,
            timestamp_ms INTEGER NOT NULL,

            price REAL NOT NULL,

            bid REAL,
            ask REAL,
            last REAL,
            spread REAL,

            volume REAL,
            volume_real REAL,
            flags INTEGER,
            is_auction INTEGER,

            buy_qty REAL,
            sell_qty REAL,

            buy_financial REAL,
            sell_financial REAL,

            source_type TEXT NOT NULL,
            source_symbol TEXT NOT NULL,
            price_source TEXT NOT NULL
        )
        """

        self.db.execute(query)

    def save_tick(
        self,
        symbol: str,
        tick: IntradayTick
    ):
        table_name = self.get_table_name(symbol)

        timestamp = datetime.fromtimestamp(
            tick.timestamp_ms / 1000,
            tz=timezone.utc
        ).isoformat()

        query = f"""
        INSERT INTO {table_name} (
            timestamp,
            timestamp_ms,
            price,
            bid,
            ask,
            last,
            spread,
            volume,
            volume_real,
            flags,
            is_auction,
            buy_qty,
            sell_qty,
            buy_financial,
            sell_financial,
            source_type,
            source_symbol,
            price_source
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?
        )
        """

        params = (
            timestamp,
            int(tick.timestamp_ms),

            float(tick.price),

            tick.bid,
            tick.ask,
            tick.last,
            tick.spread,

            tick.volume,
            tick.volume_real,
            tick.flags,
            tick.is_auction,

            tick.buy_qty,
            tick.sell_qty,

            tick.buy_financial,
            tick.sell_financial,

            tick.source_type,
            tick.source_symbol,
            tick.price_source,
        )

        self.db.execute(
            query,
            params
        )

    def count_ticks(self, symbol):
        table_name = self.get_table_name(symbol)

        result = self.db.execute(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            """
        )

        return result[0][0]

    def get_all_ticks(self, symbol):
        table_name = self.get_table_name(symbol)

        return self.db.execute(
            f"""
            SELECT *
            FROM {table_name}
            ORDER BY timestamp_ms
            """
        )

    def truncate_table(self, symbol):
        table_name = self.get_table_name(symbol)

        self.db.execute(
            f"DELETE FROM {table_name}"
        )

        self.db.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name = ?
            """,
            (table_name,)
        )