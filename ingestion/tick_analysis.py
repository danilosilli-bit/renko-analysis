from dataclasses import dataclass


@dataclass
class Aggression:

    buy_qty: float
    sell_qty: float

    buy_financial: float
    sell_financial: float

def is_auction_tick(
    bid: float,
    ask: float
) -> bool:

    if bid == 0:
        return True

    if ask == 0:
        return True

    if bid > ask:
        return True

    return False


def calculate_aggression(
    bid: float,
    ask: float,
    volume: float,
    last: float
) -> Aggression:

    if is_auction_tick(bid, ask):

        return Aggression(
            buy_qty=0.0,
            sell_qty=0.0,
            buy_financial=0.0,
            sell_financial=0.0
        )

    buy_qty = 0.0
    sell_qty = 0.0

    if last >= ask:
        buy_qty = volume

    elif last <= bid:
        sell_qty = volume

    return Aggression(
        buy_qty=buy_qty,
        sell_qty=sell_qty,
        buy_financial=round(buy_qty * last, 1),
        sell_financial=round(sell_qty * last, 1)
    )
