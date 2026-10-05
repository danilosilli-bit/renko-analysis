class Renko30RSignal:

    BRICK_SIZE = 30
    STOP_OFFSET = 20.0

    def evaluate(
        self,
        renko_service,
    ) -> dict:

        bricks = renko_service.get_bricks(
            self.BRICK_SIZE
        )

        return self.evaluate_bricks(
            bricks
        )

    def evaluate_bricks(
        self,
        bricks: list[dict],
    ) -> dict:

        if len(bricks) < 2:
            return {
                "ready": False,
                "direction": None,
                "can_buy": False,
                "can_sell": False,
                "max_stop_price": None,
                "last_brick": None,
                "previous_brick": None,
                "reason": (
                    "São necessários pelo menos "
                    "dois Renko 30R fechados."
                ),
            }

        last_brick = bricks[-1]
        previous_brick = bricks[-2]

        direction = last_brick.get(
            "direction"
        )

        if direction == "UP":

            return {
                "ready": True,
                "direction": "BUY",
                "can_buy": True,
                "can_sell": False,
                "max_stop_price": (
                    float(
                        previous_brick["low"]
                    )
                    - self.STOP_OFFSET
                ),
                "last_brick": last_brick,
                "previous_brick": previous_brick,
                "reason": (
                    "Último Renko 30R "
                    "fechado é de alta."
                ),
            }

        if direction == "DOWN":

            return {
                "ready": True,
                "direction": "SELL",
                "can_buy": False,
                "can_sell": True,
                "max_stop_price": (
                    float(
                        previous_brick["high"]
                    )
                    + self.STOP_OFFSET
                ),
                "last_brick": last_brick,
                "previous_brick": previous_brick,
                "reason": (
                    "Último Renko 30R "
                    "fechado é de baixa."
                ),
            }

        return {
            "ready": False,
            "direction": None,
            "can_buy": False,
            "can_sell": False,
            "max_stop_price": None,
            "last_brick": last_brick,
            "previous_brick": previous_brick,
            "reason": (
                "Direção do último Renko "
                "30R não reconhecida."
            ),
        }