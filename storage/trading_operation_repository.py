from pathlib import Path

from storage.sqlite_manager import (
    SQLiteManager,
)

from trading.trading_operation import (
    TradingOperation,
)


class TradingOperationRepository:

    def __init__(
        self,
        db_path: str = (
            "data/trading/trading.db"
        ),
    ):

        self.db_path = db_path

        Path(
            self.db_path
        ).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.db = SQLiteManager(
            self.db_path
        )

        self._create_table()
        self._migrate_table()


    def _create_table(
        self,
    ):

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS
            trading_operations
            (
                operation_id TEXT PRIMARY KEY,

                broker_id TEXT NOT NULL,
                feed TEXT NOT NULL,
                symbol TEXT NOT NULL,

                side TEXT NOT NULL,
                volume REAL NOT NULL,

                entry_price REAL,

                max_stop_price REAL NOT NULL,
                current_stop_price REAL NOT NULL,

                mt5_order_ticket INTEGER,
                mt5_position_ticket INTEGER,

                status TEXT NOT NULL,

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                opened_at TEXT,

                closed_at TEXT
            )
            """
        )


    def _migrate_table(
        self,
    ):

        with self.db.connect() as conn:

            cursor = conn.execute(
                """
                PRAGMA table_info(
                    trading_operations
                )
                """
            )

            rows = cursor.fetchall()

            columns = {
                row["name"]
                for row in rows
            }


            if (
                "mt5_order_ticket"
                not in columns
            ):

                conn.execute(
                    """
                    ALTER TABLE trading_operations
                    ADD COLUMN
                        mt5_order_ticket INTEGER
                    """
                )


            if (
                "mt5_position_ticket"
                not in columns
            ):

                conn.execute(
                    """
                    ALTER TABLE trading_operations
                    ADD COLUMN
                        mt5_position_ticket INTEGER
                    """
                )


            if "mt5_ticket" in columns:

                conn.execute(
                    """
                    UPDATE trading_operations
                    SET
                        mt5_order_ticket =
                            mt5_ticket
                    WHERE
                        mt5_order_ticket IS NULL
                        AND mt5_ticket IS NOT NULL
                    """
                )


    def save(
        self,
        operation: TradingOperation,
    ):

        self.db.execute(
            """
            INSERT INTO trading_operations
            (
                operation_id,
                broker_id,
                feed,
                symbol,
                side,
                volume,
                entry_price,
                max_stop_price,
                current_stop_price,
                mt5_order_ticket,
                mt5_position_ticket,
                status
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                operation.operation_id,
                operation.broker_id,
                operation.feed,
                operation.symbol,
                operation.side,
                operation.volume,
                operation.entry_price,
                operation.max_stop_price,
                operation.current_stop_price,
                operation.mt5_order_ticket,
                operation.mt5_position_ticket,
                operation.status,
            ),
        )


    def update(
        self,
        operation: TradingOperation,
    ):

        self.db.execute(
            """
            UPDATE trading_operations
            SET
                broker_id = ?,
                feed = ?,
                symbol = ?,
                side = ?,
                volume = ?,
                entry_price = ?,
                current_stop_price = ?,
                mt5_order_ticket = ?,
                mt5_position_ticket = ?,
                status = ?,

                opened_at =
                    CASE
                        WHEN
                            ? = 'OPEN'
                            AND opened_at IS NULL
                        THEN CURRENT_TIMESTAMP
                        ELSE opened_at
                    END,

                closed_at =
                    CASE
                        WHEN
                            ? = 'CLOSED'
                            AND closed_at IS NULL
                        THEN CURRENT_TIMESTAMP
                        ELSE closed_at
                    END

            WHERE operation_id = ?
            """,
            (
                operation.broker_id,
                operation.feed,
                operation.symbol,
                operation.side,
                operation.volume,
                operation.entry_price,

                # max_stop_price não aparece
                # no UPDATE de propósito.
                operation.current_stop_price,

                operation.mt5_order_ticket,
                operation.mt5_position_ticket,
                operation.status,

                operation.status,
                operation.status,

                operation.operation_id,
            ),
        )


    def get(
        self,
        operation_id: str,
    ) -> TradingOperation | None:

        rows = self.db.execute(
            """
            SELECT *
            FROM trading_operations
            WHERE operation_id = ?
            """,
            (
                operation_id,
            ),
        )

        if not rows:
            return None

        return self._row_to_operation(
            rows[0]
        )


    def get_all(
        self,
    ) -> list[TradingOperation]:

        rows = self.db.execute(
            """
            SELECT *
            FROM trading_operations
            ORDER BY created_at, operation_id
            """
        )

        return [
            self._row_to_operation(
                row
            )
            for row in rows
        ]


    def get_active(
        self,
    ) -> list[TradingOperation]:

        rows = self.db.execute(
            """
            SELECT *
            FROM trading_operations
            WHERE status IN (
                'PENDING',
                'OPEN',
                'RECONCILE'
            )
            ORDER BY created_at, operation_id
            """
        )

        return [
            self._row_to_operation(
                row
            )
            for row in rows
        ]


    def _row_to_operation(
        self,
        row,
    ) -> TradingOperation:

        return TradingOperation(
            operation_id=
                row["operation_id"],

            broker_id=
                row["broker_id"],

            feed=
                row["feed"],

            symbol=
                row["symbol"],

            side=
                row["side"],

            volume=
                float(
                    row["volume"]
                ),

            entry_price=(
                float(
                    row["entry_price"]
                )
                if row["entry_price"]
                is not None
                else None
            ),

            max_stop_price=
                float(
                    row[
                        "max_stop_price"
                    ]
                ),

            current_stop_price=
                float(
                    row[
                        "current_stop_price"
                    ]
                ),

            mt5_order_ticket=(
                int(
                    row[
                        "mt5_order_ticket"
                    ]
                )
                if row[
                    "mt5_order_ticket"
                ] is not None
                else None
            ),

            mt5_position_ticket=(
                int(
                    row[
                        "mt5_position_ticket"
                    ]
                )
                if row[
                    "mt5_position_ticket"
                ] is not None
                else None
            ),

            status=
                row["status"],
        )