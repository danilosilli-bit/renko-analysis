class RenkoRepository:

    def __init__(self, db_manager):
        self.db = db_manager

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

    def create_state_table(self):

        query = f"""
        CREATE TABLE IF NOT EXISTS renko_state (

            symbol TEXT PRIMARY KEY,

            brick_size REAL,

            open_time TEXT,

            open REAL,
            last REAL,

            high REAL,
            low REAL,

            direction TEXT,

            volume REAL,

            buy_qty REAL,
            sell_qty REAL,

            buy_financial REAL,
            sell_financial REAL,

            trades_count INTEGER,

            UNIQUE(symbol)
        )
        """

        self.db.execute(query)

    def save_brick(self, symbol, brick):
        table_name = self.get_table_name(symbol)

        query = f""" INSERT INTO {table_name} (
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
        params = (
                float(brick['brick_size']),
                str(brick['open_time']),
                str(brick['close_time']),
                float(brick['open']),
                float(brick['close']),
                float(brick['high']),
                float(brick['low']),
                str(brick['direction']),
                int(brick['volume']),
                float(brick['buy_qty']),
                float(brick['sell_qty']),
                float(brick['buy_financial']),
                float(brick['sell_financial']),
                int(brick['trades_count']),
            )


        self.db.execute(query, params)

    def save_state(self, state):
        query = f""" INSERT OR REPLACE INTO renko_state (
            symbol,
            brick_size,
            open_time,
            open,
            last,
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
        params = (
                str(state.symbol),
                float(state.brick_size),
                str(state.open_time),
                float(state.open),
                float(state.last),
                float(state.high),
                float(state.low),
                str(state.direction),
                int(state.volume),
                float(state.buy_qty),
                float(state.sell_qty),
                float(state.buy_financial),
                float(state.sell_financial),
                int(state.trades_count),
            )
        

        self.db.execute(query, params)

    def get_state(self, symbol, brick_size):
        
        query = """
            SELECT *
            FROM renko_state
            WHERE symbol = ?
            AND brick_size = ?
            LIMIT 1
        """

        result = self.db.execute(
            query,
            (symbol, brick_size)
        )


        return result[0] if result else None
    

    def get_last_closed_brick(self, symbol, brick_size):

        table_name = self.get_table_name(symbol)

        query = f"""
            SELECT *
            FROM {table_name}
            WHERE brick_size = ?
            ORDER BY close_time DESC
            LIMIT 1
        """

        result = self.db.execute(
            query,
            (brick_size,)
        )

        return result[0] if result else None


    def get_table_name(self, symbol):
        return f"renko_{symbol.lower()}"
    

