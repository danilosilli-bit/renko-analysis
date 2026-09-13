class SourceHandoffService:

    def __init__(
        self,
        last_bootstrap_timestamp_ms=None,
        from_source: str = "",
        from_symbol: str = "",
        to_source: str = "",
        to_symbol: str = "",
    ):
        self.last_bootstrap_timestamp_ms = (
            last_bootstrap_timestamp_ms
        )

        self.from_source = from_source
        self.from_symbol = from_symbol

        self.to_source = to_source
        self.to_symbol = to_symbol

        self.completed = False
        self.first_realtime_timestamp_ms = None

    def accept_realtime_tick(
        self,
        timestamp_ms: int,
    ) -> dict:
        """
        Registra a transição entre a fonte do bootstrap
        e a fonte realtime.

        Retorna também se o tick é o primeiro tick
        da transição.
        """

        if self.completed:
            return {
                "accepted": True,
                "source_transition": False,
            }

        self.first_realtime_timestamp_ms = (
            timestamp_ms
        )

        print("")
        print("HANDOFF concluído")
        print("=" * 40)

        print(
            f"from_source   : {self.from_source}"
        )

        print(
            f"from_symbol   : {self.from_symbol}"
        )

        print(
            f"to_source     : {self.to_source}"
        )

        print(
            f"to_symbol     : {self.to_symbol}"
        )

        print(
            "bootstrap_last : "
            f"{self.last_bootstrap_timestamp_ms}"
        )

        print(
            "realtime_first : "
            f"{self.first_realtime_timestamp_ms}"
        )

        self.completed = True

        return {
            "accepted": True,
            "source_transition": True,
        }