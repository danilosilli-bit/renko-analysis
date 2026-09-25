class BrokerRouter:

    def __init__(self):
        self._brokers = {}


    def register(
        self,
        broker_id: str,
        feed_service,
        feed: str,
        symbol: str,
    ):
        broker_id = (
            broker_id
            .strip()
            .lower()
        )

        feed = (
            feed
            .strip()
            .upper()
        )

        if not broker_id:
            raise ValueError(
                "broker_id não pode ser vazio."
            )

        if not feed:
            raise ValueError(
                "feed não pode ser vazio."
            )

        self._brokers[broker_id] = {
            "feed_service": feed_service,
            "feed": feed,
            "symbol": symbol,
        }


    def get(
        self,
        broker_id: str,
    ):

        broker_id = (
            broker_id
            .strip()
            .lower()
        )

        broker = self._brokers.get(
            broker_id
        )

        if broker is None:
            raise ValueError(
                f"Broker não configurado: "
                f"{broker_id}"
            )

        return broker


    def get_feed_service(
        self,
        broker_id: str,
    ):

        return self.get(
            broker_id
        )["feed_service"]


    def get_feed(
        self,
        broker_id: str,
    ) -> str:

        return self.get(
            broker_id
        )["feed"]


    def get_symbol(
        self,
        broker_id: str,
    ) -> str:

        return self.get(
            broker_id
        )["symbol"]


    def has_broker(
        self,
        broker_id: str,
    ) -> bool:

        broker_id = (
            broker_id
            .strip()
            .lower()
        )

        return (
            broker_id
            in self._brokers
        )