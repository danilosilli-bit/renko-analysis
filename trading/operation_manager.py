import uuid

from trading.trading_operation import (
    TradingOperation,
)


class OperationManager:

    def __init__(
        self,
        repository=None,
    ):

        self.repository = repository

        self._operations = {}


        if self.repository is not None:

            active_operations = (
                self.repository
                .get_active()
            )

            for operation in active_operations:

                self._operations[
                    operation.operation_id
                ] = operation


    def create_operation(
        self,
        broker_id: str,
        feed: str,
        symbol: str,
        side: str,
        volume: float,
        max_stop_price: float,
    ) -> TradingOperation:

        side = side.upper().strip()
        feed = feed.upper().strip()

        if side not in (
            "BUY",
            "SELL",
        ):
            raise ValueError(
                "side deve ser BUY ou SELL."
            )

        if volume <= 0:
            raise ValueError(
                "volume deve ser maior que zero."
            )

        if max_stop_price is None:
            raise ValueError(
                "max_stop_price é obrigatório."
            )


        operation_id = str(
            uuid.uuid4()
        )


        operation = TradingOperation(
            operation_id=operation_id,
            broker_id=broker_id,
            feed=feed,
            symbol=symbol,
            side=side,
            volume=float(volume),

            entry_price=None,

            max_stop_price=float(
                max_stop_price
            ),

            current_stop_price=float(
                max_stop_price
            ),

            mt5_order_ticket=None,
            mt5_position_ticket=None,

            status="PENDING",
        )


        self._operations[
            operation_id
        ] = operation


        if self.repository is not None:

            self.repository.save(
                operation
            )


        return operation


    def get_operation(
        self,
        operation_id: str,
    ) -> TradingOperation | None:

        return self._operations.get(
            operation_id
        )


    def get_operations(
        self,
    ) -> list[TradingOperation]:

        return list(
            self._operations.values()
        )


    def get_open_operations(
        self,
    ) -> list[TradingOperation]:

        return [
            operation
            for operation
            in self._operations.values()
            if operation.status
            in (
                "PENDING",
                "OPEN",
                "RECONCILE",
            )
        ]


    def find_open_by_mt5_position_ticket(
        self,
        mt5_position_ticket: int,
    ) -> list[TradingOperation]:

        mt5_position_ticket = int(
            mt5_position_ticket
        )

        return [
            operation
            for operation
            in self._operations.values()
            if (
                operation.status == "OPEN"
                and
                operation.mt5_position_ticket
                == mt5_position_ticket
            )
        ]


    def mark_open(
        self,
        operation_id: str,
        entry_price: float,
        mt5_order_ticket: int,
        mt5_position_ticket: int | None = None,
    ) -> TradingOperation:

        operation = (
            self._require_operation(
                operation_id
            )
        )

        operation.entry_price = float(
            entry_price
        )

        operation.mt5_order_ticket = int(
            mt5_order_ticket
        )

        if mt5_position_ticket is not None:

            operation.mt5_position_ticket = int(
                mt5_position_ticket
            )

        operation.status = "OPEN"


        if self.repository is not None:

            self.repository.update(
                operation
            )


        return operation


    def set_mt5_position_ticket(
        self,
        operation_id: str,
        mt5_position_ticket: int,
    ) -> TradingOperation:

        operation = (
            self._require_operation(
                operation_id
            )
        )

        operation.mt5_position_ticket = int(
            mt5_position_ticket
        )


        if self.repository is not None:

            self.repository.update(
                operation
            )


        return operation


    def mark_closed(
        self,
        operation_id: str,
    ) -> TradingOperation:

        operation = (
            self._require_operation(
                operation_id
            )
        )

        operation.status = "CLOSED"


        if self.repository is not None:

            self.repository.update(
                operation
            )


        return operation


    def update_current_stop(
        self,
        operation_id: str,
        new_stop_price: float,
    ) -> bool:

        operation = (
            self._require_operation(
                operation_id
            )
        )


        updated = (
            operation.update_current_stop(
                new_stop_price
            )
        )


        if (
            updated
            and
            self.repository is not None
        ):

            self.repository.update(
                operation
            )


        return updated


    def mark_reconcile(
        self,
        operation_id: str,
    ) -> TradingOperation:

        operation = (
            self._require_operation(
                operation_id
            )
        )

        operation.status = "RECONCILE"


        if self.repository is not None:

            self.repository.update(
                operation
            )


        return operation


    def mark_failed(
        self,
        operation_id: str,
    ) -> TradingOperation:

        operation = (
            self._require_operation(
                operation_id
            )
        )

        operation.status = "FAILED"


        if self.repository is not None:

            self.repository.update(
                operation
            )


        return operation


    def _require_operation(
        self,
        operation_id: str,
    ) -> TradingOperation:

        operation = self.get_operation(
            operation_id
        )

        if operation is None:
            raise ValueError(
                "Operação não encontrada: "
                f"{operation_id}"
            )

        return operation