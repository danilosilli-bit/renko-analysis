

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
            volume_real REAL
        )
        """

        self.db.execute(query)


    def save_ticks(self, symbol, ticks):
        table_name = self.get_table_name(symbol)

        """
        Save normalized ticks into the symbol table.
        """
        query = f""" INSERT INTO {table_name} (
            timestamp,
            timestamp_ms,
            bid,
            ask,
            last,
            volume, 
            flags,
            volume_real
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        ticks_tuple = [
            (
                str(tick['timestamp']),
                str(tick['timestamp_ms']),
                float(tick['bid']),
                float(tick['ask']),
                float(tick['last']),
                int(tick['volume']),
                int(tick['flags']),
                float(tick['volume_real'])
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
        ORDER BY timestamp
        """

        return self.db.execute(
            query,
            (start_date, end_date)
        )

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