from storage.renko_repository import (
    RenkoRepository,
)


class IntradayRenkoRepository(
    RenkoRepository
):

    def create_renko_table(
        self,
        symbol,
    ):
        table_name = self.get_table_name(
            symbol
        )

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

            trades_count INTEGER,

            source_transition INTEGER
                NOT NULL DEFAULT 0
        )
        """

        self.db.execute(query)


    def save_brick(
        self,
        symbol,
        brick,
    ):
        table_name = self.get_table_name(
            symbol
        )

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
            trades_count,
            source_transition
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?
        )
        """

        params = (
            float(brick["brick_size"]),
            str(brick["open_time"]),
            str(brick["close_time"]),
            float(brick["open"]),
            float(brick["close"]),
            float(brick["high"]),
            float(brick["low"]),
            str(brick["direction"]),
            int(brick["volume"]),
            float(brick["buy_qty"]),
            float(brick["sell_qty"]),
            float(
                brick["buy_financial"]
            ),
            float(
                brick["sell_financial"]
            ),
            int(brick["trades_count"]),
            int(
                bool(
                    brick.get(
                        "source_transition",
                        False,
                    )
                )
            ),
        )

        self.db.execute(
            query,
            params,
        )