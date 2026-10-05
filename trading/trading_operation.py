from dataclasses import dataclass
from typing import Optional


@dataclass
class TradingOperation:

    operation_id: str

    broker_id: str
    feed: str
    symbol: str

    side: str
    volume: float

    entry_price: Optional[float]

    max_stop_price: float
    current_stop_price: float

    mt5_order_ticket: Optional[int]
    mt5_position_ticket: Optional[int]

    status: str = "PENDING"


    def update_current_stop(
        self,
        new_stop_price: float,
    ) -> bool:

        new_stop_price = float(
            new_stop_price
        )


        if self.side == "BUY":

            # BUY:
            # nunca pode ficar abaixo
            # do stop máximo original.
            if (
                new_stop_price
                <
                self.max_stop_price
            ):
                return False

            # Depois que o stop sobe,
            # não pode voltar para baixo.
            if (
                new_stop_price
                <
                self.current_stop_price
            ):
                return False


        elif self.side == "SELL":

            # SELL:
            # nunca pode ficar acima
            # do stop máximo original.
            if (
                new_stop_price
                >
                self.max_stop_price
            ):
                return False

            # Depois que o stop desce,
            # não pode voltar para cima.
            if (
                new_stop_price
                >
                self.current_stop_price
            ):
                return False


        else:

            return False


        self.current_stop_price = (
            new_stop_price
        )

        return True