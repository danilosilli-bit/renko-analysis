class OrderGuard:

    def __init__(
        self,
        signal_provider,
    ):
        self.signal_provider = (
            signal_provider
        )


    def validate_entry(
        self,
        feed: str,
        side: str,
    ) -> dict:

        feed = feed.upper().strip()
        side = side.upper().strip()

        try:

            signal = (
                self.signal_provider(
                    feed
                )
            )

        except Exception as exc:

            return {
                "allowed": False,
                "feed": feed,
                "side": side,
                "reason":
                    "Falha ao obter sinal 30R.",
                "error": str(exc),
            }


        if not signal:

            return {
                "allowed": False,
                "feed": feed,
                "side": side,
                "reason":
                    "Sinal 30R indisponível.",
            }


        if signal.get("ready") is not True:

            return {
                "allowed": False,
                "feed": feed,
                "side": side,
                "reason":
                    "Sinal 30R não está pronto.",
                "signal": signal,
            }


        if side == "BUY":

            allowed = (
                signal.get("can_buy")
                is True
            )

        elif side == "SELL":

            allowed = (
                signal.get("can_sell")
                is True
            )

        else:

            return {
                "allowed": False,
                "feed": feed,
                "side": side,
                "reason":
                    "Lado da ordem inválido.",
                "signal": signal,
            }


        if not allowed:

            return {
                "allowed": False,
                "feed": feed,
                "side": side,
                "direction":
                    signal.get(
                        "direction"
                    ),
                "max_stop_price":
                    signal.get(
                        "max_stop_price"
                    ),
                "reason":
                    (
                        f"Ordem {side} bloqueada "
                        f"pelo Renko 30R."
                    ),
                "signal": signal,
            }


        return {
            "allowed": True,
            "feed": feed,
            "side": side,
            "direction":
                signal.get(
                    "direction"
                ),
            "max_stop_price":
                signal.get(
                    "max_stop_price"
                ),
            "reason":
                (
                    f"Ordem {side} autorizada "
                    f"pelo Renko 30R."
                ),
            "signal": signal,
        }