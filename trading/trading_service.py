from trading.broker_router import BrokerRouter


class TradingService:

    def __init__(
        self,
        broker_router: BrokerRouter,
        broker_id: str,
    ):
        self.broker_router = broker_router
        self.broker_id = broker_id


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


            return {
                "status": "OK",
                "broker":
                    selected_broker_id,
                "symbol": symbol,
                "side": side,
                "volume": volume,
                "check_only": check_only,
                "request_id": request_id,
                "result":
                    message.get("result"),
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


    def close_position(
        self,
        ticket: int,
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


            if ticket <= 0:
                return {
                    "status": "ERROR",
                    "message":
                        "ticket deve ser maior que zero.",
                }


            request_id = (
                feed_service
                .close_position(
                    ticket=ticket,
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
                return {
                    "status": "TIMEOUT",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "ticket": ticket,
                    "check_only": check_only,
                    "request_id": request_id,
                }


            if message.get("error"):
                return {
                    "status": "ERROR",
                    "broker":
                        selected_broker_id,
                    "symbol": symbol,
                    "ticket": ticket,
                    "check_only": check_only,
                    "request_id": request_id,
                    "message":
                        message.get("error"),
                }


            return {
                "status": "OK",
                "broker":
                    selected_broker_id,
                "symbol": symbol,
                "ticket": ticket,
                "check_only": check_only,
                "request_id": request_id,
                "result":
                    message.get("result"),
            }


        except Exception as exc:

            return {
                "status": "ERROR",
                "message": str(exc),
            }
