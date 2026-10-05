from trading.broker_router import BrokerRouter


class TradingService:

    def __init__(
        self,
        broker_router: BrokerRouter,
        broker_id: str,
        order_guard=None,
        operation_manager=None,
    ):
        self.broker_router = broker_router
        self.broker_id = broker_id
        self.order_guard = order_guard
        self.operation_manager = (
            operation_manager
        )


    def _get_broker(self):

        return self.broker_router.get(
            self.broker_id
        )


    def _validate_feed(
        self,
        feed_service,
    ):

        if feed_service is None:
            return {
                "status": "ERROR",
                "message":
                    "Feed de trading não iniciado.",
            }

        if not feed_service.running:
            return {
                "status": "ERROR",
                "message":
                    "Feed de trading não está rodando.",
            }

        return None

    def send_market_order(
        self,
        side: str,
        volume: float = 1,
        check_only: bool = True,
        broker_id: str | None = None,
    ):

        try:

            if broker_id is None:
                selected_broker_id = (
                    self.broker_id
                )
            else:
                selected_broker_id = (
                    broker_id
                )

            broker = (
                self.broker_router.get(
                    selected_broker_id
                )
            )

            feed_service = (
                broker["feed_service"]
            )

            feed = (
                broker["feed"]
            )

            symbol = (
                broker["symbol"]
            )


            feed_error = (
                self._validate_feed(
                    feed_service
                )
            )

            if feed_error is not None:
                return feed_error


            side = side.upper().strip()

            if side not in (
                "BUY",
                "SELL",
            ):
                return {
                    "status": "ERROR",
                    "message":
                        "side deve ser BUY ou SELL.",
                }


            if volume <= 0:
                return {
                    "status": "ERROR",
                    "message":
                        "volume deve ser maior que zero.",
                }


            # Fail-closed:
            # nenhuma nova entrada pode passar
            # sem OrderGuard configurado.
            if self.order_guard is None:
                return {
                    "status": "BLOCKED",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "feed": feed,
                    "side": side,
                    "volume": volume,
                    "check_only": check_only,
                    "message":
                        "OrderGuard não configurado. "
                        "Nova entrada bloqueada.",
                }


            guard_result = (
                self.order_guard
                .validate_entry(
                    feed=feed,
                    side=side,
                )
            )


            if (
                guard_result.get(
                    "allowed"
                )
                is not True
            ):
                return {
                    "status": "BLOCKED",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "feed": feed,
                    "side": side,
                    "volume": volume,
                    "check_only": check_only,
                    "message":
                        guard_result.get(
                            "reason",
                            "Ordem bloqueada.",
                        ),
                    "guard":
                        guard_result,
                }


            operation = None

            if not check_only:

                if self.operation_manager is None:
                    return {
                        "status": "ERROR",
                        "broker":
                            selected_broker_id,
                        "symbol": symbol,
                        "feed": feed,
                        "side": side,
                        "volume": volume,
                        "check_only":
                            check_only,
                        "message":
                            "OperationManager "
                            "não configurado.",
                    }

                max_stop_price = (
                    guard_result.get(
                        "max_stop_price"
                    )
                )

                if max_stop_price is None:
                    return {
                        "status": "BLOCKED",
                        "broker":
                            selected_broker_id,
                        "symbol": symbol,
                        "feed": feed,
                        "side": side,
                        "volume": volume,
                        "check_only":
                            check_only,
                        "message":
                            "OrderGuard não "
                            "forneceu "
                            "max_stop_price.",
                        "guard":
                            guard_result,
                    }

                operation = (
                    self.operation_manager
                    .create_operation(
                        broker_id=(
                            selected_broker_id
                        ),
                        feed=feed,
                        symbol=symbol,
                        side=side,
                        volume=volume,
                        max_stop_price=(
                            max_stop_price
                        ),
                    )
                )


            request_id = (
                feed_service
                .send_market_order(
                    side=side,
                    volume=volume,
                    check_only=check_only,
                    feed=feed,
                )
            )


            message = (
                feed_service
                .wait_for_command_result(
                    request_id=request_id,
                    timeout=3.0,
                )
            )


            if message is None:

                if (
                    not check_only
                    and operation is not None
                ):
                    self.operation_manager.mark_reconcile(
                        operation.operation_id
                    )

                return {
                    "status": "TIMEOUT",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "side": side,
                    "volume": volume,
                    "check_only": check_only,
                    "request_id": request_id,
                }


            if message.get("error"):

                if (
                    not check_only
                    and operation is not None
                ):
                    self.operation_manager.mark_reconcile(
                        operation.operation_id
                    )

                return {
                    "status": "ERROR",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "side": side,
                    "volume": volume,
                    "check_only": check_only,
                    "request_id": request_id,
                    "message":
                        message.get("error"),
                }


            worker_result = (
                message.get("result")
            )

            if (
                not check_only
                and operation is not None
                and worker_result is not None
            ):

                if (
                    worker_result.get("success")
                        is False
                    and worker_result.get("stage")
                        == "check"
                ):
                    self.operation_manager.mark_failed(
                        operation.operation_id
                    )

                elif (
                    worker_result.get("stage")
                        == "send"
                ):

                    if (
                        worker_result.get("success")
                        is True
                    ):

                        mt5_result = (
                            worker_result.get("result")
                            or {}
                        )

                        mt5_order_ticket = (
                            mt5_result.get("order")
                        )

                        mt5_position_ticket = (
                            worker_result.get(
                                "position_ticket"
                            )
                        )

                        entry_price = (
                            mt5_result.get("price")
                        )

                        if (
                            mt5_order_ticket
                            and
                            mt5_position_ticket
                            and
                            entry_price is not None
                        ):
                            self.operation_manager.mark_open(
                                operation_id=(
                                    operation.operation_id
                                ),
                                entry_price=entry_price,
                                mt5_order_ticket=(
                                    mt5_order_ticket
                                ),
                                mt5_position_ticket=(
                                    mt5_position_ticket
                                ),
                            )

                        else:
                            self.operation_manager.mark_reconcile(
                                operation.operation_id
                            )

                    else:
                        self.operation_manager.mark_reconcile(
                            operation.operation_id
                        )

            return {
                "status": "OK",
                "broker":
                    selected_broker_id,
                "symbol": symbol,
                "side": side,
                "volume": volume,
                "check_only": check_only,
                "request_id": request_id,

                # Guardamos na resposta a referência
                # usada para autorizar esta entrada.
                "guard":
                    guard_result,

                "result":
                    worker_result,
            }


        except Exception as exc:

            return {
                "status": "ERROR",
                "message": str(exc),
            }


    def get_positions(
        self,
        broker_id: str | None = None,
    ):

        try:

            if broker_id is None:
                selected_broker_id = (
                    self.broker_id
                )
            else:
                selected_broker_id = (
                    broker_id
                )

            broker = (
                self.broker_router.get(
                    selected_broker_id
                )
            )

            feed_service = (
                broker["feed_service"]
            )

            feed = (
                broker["feed"]
            )

            symbol = (
                broker["symbol"]
            )

            feed_error = (
                self._validate_feed(
                    feed_service
                )
            )

            if feed_error is not None:
                return feed_error


            request_id = (
                feed_service
                .get_positions(
                    feed=feed
                )
            )


            message = (
                feed_service
                .wait_for_command_result(
                    request_id=request_id,
                    timeout=3.0,
                )
            )


            if message is None:
                return {
                    "status": "TIMEOUT",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "request_id": request_id,
                }


            if message.get("error"):
                return {
                    "status": "ERROR",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "request_id": request_id,
                    "message":
                        message.get("error"),
                }


            return {
                "status": "OK",
                "broker":
                    selected_broker_id,
                "symbol": symbol,
                "positions":
                    message.get(
                        "positions",
                        [],
                    ),
                "request_id": request_id,
            }


        except Exception as exc:

            return {
                "status": "ERROR",
                "message": str(exc),
            }

    def get_open_operations(
        self,
        expected_feed: str | None = None,
    ):

        try:

            if self.operation_manager is None:
                return {
                    "status": "ERROR",
                    "message":
                        "OperationManager não configurado.",
                }


            operations = (
                self.operation_manager
                .get_open_operations()
            )


            if expected_feed is not None:

                expected_feed = (
                    expected_feed
                    .upper()
                    .strip()
                )

                operations = [
                    operation
                    for operation in operations
                    if (
                        operation.feed
                        .upper()
                        .strip()
                        == expected_feed
                    )
                ]


            items = []

            for operation in operations:

                items.append(
                    {
                        "operation_id":
                            operation.operation_id,

                        "broker_id":
                            operation.broker_id,

                        "feed":
                            operation.feed,

                        "symbol":
                            operation.symbol,

                        "side":
                            operation.side,

                        "volume":
                            operation.volume,

                        "entry_price":
                            operation.entry_price,

                        "max_stop_price":
                            operation.max_stop_price,

                        "current_stop_price":
                            operation.current_stop_price,

                        "mt5_order_ticket":
                            operation.mt5_order_ticket,

                        "mt5_position_ticket":
                            operation.mt5_position_ticket,

                        "status":
                            operation.status,
                    }
                )


            return {
                "status": "OK",
                "operations": items,
            }


        except Exception as exc:

            return {
                "status": "ERROR",
                "message": str(exc),
            }

    def close_position(
        self,
        operation_id: str,
        check_only: bool = True,
        expected_feed: str | None = None,
    ):

        try:

            if self.operation_manager is None:
                return {
                    "status": "ERROR",
                    "message":
                        "OperationManager não configurado.",
                }


            operation = (
                self.operation_manager
                .get_operation(
                    operation_id
                )
            )

            if operation is None:
                return {
                    "status": "ERROR",
                    "message":
                        "Operação não encontrada.",
                }


            if operation.status != "OPEN":
                return {
                    "status": "ERROR",
                    "message":
                        "Operação não está aberta.",
                    "operation_id":
                        operation.operation_id,
                    "operation_status":
                        operation.status,
                }


            if expected_feed is not None:

                expected_feed = (
                    expected_feed
                    .upper()
                    .strip()
                )

                if (
                    operation.feed
                    .upper()
                    .strip()
                    != expected_feed
                ):
                    return {
                        "status": "ERROR",
                        "message":
                            "Operação pertence a outro "
                            "mercado.",
                        "operation_id":
                            operation.operation_id,
                        "operation_feed":
                            operation.feed,
                        "expected_feed":
                            expected_feed,
                    }


            if (
                operation.mt5_position_ticket
                is None
            ):
                return {
                    "status": "ERROR",
                    "message":
                        "Operação não possui "
                        "mt5_position_ticket.",
                    "operation_id":
                        operation.operation_id,
                }


            if operation.volume <= 0:
                return {
                    "status": "ERROR",
                    "message":
                        "Volume da operação deve ser "
                        "maior que zero.",
                    "operation_id":
                        operation.operation_id,
                }


            selected_broker_id = (
                operation.broker_id
            )

            broker = (
                self.broker_router.get(
                    selected_broker_id
                )
            )

            feed_service = (
                broker["feed_service"]
            )

            feed = (
                broker["feed"]
            )

            symbol = (
                broker["symbol"]
            )


            if (
                feed.upper().strip()
                !=
                operation.feed.upper().strip()
            ):
                return {
                    "status": "ERROR",
                    "message":
                        "Feed da operação não corresponde "
                        "ao broker configurado.",
                    "operation_id":
                        operation.operation_id,
                }


            if (
                symbol
                !=
                operation.symbol
            ):
                return {
                    "status": "ERROR",
                    "message":
                        "Símbolo da operação não corresponde "
                        "ao broker configurado.",
                    "operation_id":
                        operation.operation_id,
                }


            feed_error = (
                self._validate_feed(
                    feed_service
                )
            )

            if feed_error is not None:
                return feed_error


            ticket = int(
                operation.mt5_position_ticket
            )

            volume = float(
                operation.volume
            )


            request_id = (
                feed_service
                .close_position(
                    ticket=ticket,
                    volume=volume,
                    check_only=check_only,
                    feed=feed,
                )
            )


            message = (
                feed_service
                .wait_for_command_result(
                    request_id=request_id,
                    timeout=3.0,
                )
            )


            if message is None:

                if not check_only:
                    self.operation_manager.mark_reconcile(
                        operation.operation_id
                    )

                return {
                    "status": "TIMEOUT",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "operation_id":
                        operation.operation_id,
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "request_id": request_id,
                }


            if message.get("error"):

                if not check_only:
                    self.operation_manager.mark_reconcile(
                        operation.operation_id
                    )

                return {
                    "status": "ERROR",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "operation_id":
                        operation.operation_id,
                    "ticket": ticket,
                    "volume": volume,
                    "check_only": check_only,
                    "request_id": request_id,
                    "message":
                        message.get("error"),
                }


            worker_result = (
                message.get("result")
            )


            if (
                not check_only
                and worker_result is not None
                and worker_result.get("success")
                    is True
                and worker_result.get("stage")
                    == "send"
            ):
                self.operation_manager.mark_closed(
                    operation.operation_id
                )


            return {
                "status": "OK",
                "broker":
                    selected_broker_id,
                "symbol": symbol,
                "operation_id":
                    operation.operation_id,
                "ticket": ticket,
                "volume": volume,
                "check_only": check_only,
                "request_id": request_id,
                "result":
                    worker_result,
            }


        except Exception as exc:

            return {
                "status": "ERROR",
                "message": str(exc),
            }