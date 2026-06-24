import numpy as np

class TickRepository:

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
            timestamp_ms TEXT NOT NULL,

            bid REAL,
            ask REAL,
            last REAL,

            volume INTEGER,
            flags INTEGER,
            volume_real REAL,

            is_auction INTEGER,

            buy_qty REAL,
            sell_qty REAL,

            buy_financial REAL,
            sell_financial REAL
        )
        """

        self.db.execute(query)

    def save_ticks(self, symbol, ticks):
        table_name = self.get_table_name(symbol)

        query = f"""
        INSERT INTO {table_name} (
            timestamp,
            timestamp_ms,
            bid,
            ask,
            last,
            volume,
            flags,
            volume_real,
            is_auction,
            buy_qty,
            sell_qty,
            buy_financial,
            sell_financial
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        ticks_tuple = [
            (
                str(tick["timestamp"]),
                str(tick["timestamp_ms"]),
                float(tick["bid"]),
                float(tick["ask"]),
                float(tick["last"]),
                int(tick["volume"]),
                int(tick["flags"]),
                float(tick["volume_real"]),
                int(tick["is_auction"]),
                float(tick["buy_qty"]),
                float(tick["sell_qty"]),
                float(tick["buy_financial"]),
                float(tick["sell_financial"]),
            )
            for tick in ticks
        ]

        self.db.executemany(query, ticks_tuple)

    def get_ticks(self, symbol, start_date, end_date):
        table_name = self.get_table_name(symbol)

        query = f"""
        SELECT *
        FROM {table_name}
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp_ms
        """

        rows = self.db.execute(
            query,
            (start_date, end_date)
        )

        return self._convert_rows_to_ticks(rows)

    def count_ticks(self, symbol):
        table_name = self.get_table_name(symbol)

        query = f"""
        SELECT COUNT(*)
        FROM {table_name}
        """

        result = self.db.execute(query)

        return result[0][0]

    def truncate_table(self, symbol):
        table_name = self.get_table_name(symbol)

        self.db.execute(
            f"DELETE FROM {table_name}"
        )

        self.db.execute(
            f"DELETE FROM sqlite_sequence WHERE name='{table_name}'"
        )

    def drop_table(self, symbol):
        table_name = self.get_table_name(symbol)

        self.db.execute(
            f"DROP TABLE IF EXISTS {table_name}"
        )

    def get_all_ticks(self, symbol):
        table_name = self.get_table_name(symbol)

        query = f"""
        SELECT *
        FROM {table_name}
        ORDER BY timestamp_ms
        """

        rows = self.db.execute(query)

        return self._convert_rows_to_ticks(rows)

    def get_ticks_by_day(self, symbol, target_date):
        table_name = self.get_table_name(symbol)

        start_date = f"{target_date}T00:00:00"
        end_date = f"{target_date}T23:59:59"

        query = f"""
        SELECT *
        FROM {table_name}
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp_ms
        """

        rows = self.db.execute(
            query,
            (start_date, end_date)
        )

        return self._convert_rows_to_ticks(rows)

    def has_ticks_for_day(self, symbol, target_date):
        table_name = self.get_table_name(symbol)

        start_date = f"{target_date} 00:00:00"
        end_date = f"{target_date} 23:59:59"

        query = f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE timestamp BETWEEN ? AND ?
        """

        result = self.db.execute(
            query,
            (start_date, end_date)
        )

        return result[0][0] > 0
    
    def _convert_rows_to_ticks(self, rows):
        ticks = []

        for row in rows:
            tick = dict(row)

            tick["timestamp"] = np.datetime64(tick["timestamp"])
            tick["timestamp_ms"] = np.datetime64(tick["timestamp_ms"])

            ticks.append(tick)

        return ticks