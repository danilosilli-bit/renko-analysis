import numpy as np

from renko.renko_brick import RenkoBrick
from renko.renko_state import RenkoState
from market.instrument_config import InstrumentConfig
from storage.tick_repository import TickRepository



class RenkoEngine:

    def __init__(
        self,
        symbol,
        brick_size,
        renko_repository,
        persist_state_every_tick=False
    ):
        self.symbol = symbol
        self.brick_size = brick_size

        self.repository = renko_repository

        self.instrument = InstrumentConfig.from_symbol(
            symbol
        )
        self.state = None
        self.last_closed_brick = None
        self.persist_state_every_tick = persist_state_every_tick        

    def process_tick(self, tick):

        if self.state is None:
            self._initialize_state(tick)

        close_type, qty_bricks = self._check_brick_close(
            tick,
            self.brick_size
        )

        if close_type != "NO_CLOSE" and qty_bricks > 0:

            if qty_bricks == 1:
                closed_brick = self._build_closed_brick(
                    close_type,
                    tick["timestamp_ms"]
                )

                if closed_brick:
                    self.repository.save_brick(
                        self.symbol,
                        closed_brick
                    )

                    self.last_closed_brick = closed_brick

                    self._reset_state_after_close(
                        tick,
                        closed_brick["close"]
                    )

            else:
                closed_bricks = self._build_closed_bricks(
                    close_type,
                    qty_bricks,
                    tick
                )

                if closed_bricks:
                    for brick in closed_bricks:
                        self.repository.save_brick(
                            self.symbol,
                            brick
                        )

                    self.last_closed_brick = closed_bricks[-1]

                    self._reset_state_after_close(
                        tick,
                        closed_bricks[-1]["close"]
                    )

            return

        self._update_current_brick(tick)



    def _update_current_brick(self, tick):
        last = self._round_price(tick["last"])

        
        low, high = self._update_low_high(
            self.state.low,
            self.state.high,
            last
        )
        self.state.low = low
        self.state.high = high

        
        self.state.last = last

        
        if self.state.open_time is None:
            self.state.open_time = tick["timestamp_ms"]

        
        self.state.volume += tick["volume"]
        self.state.buy_qty += tick["buy_qty"]
        self.state.sell_qty += tick["sell_qty"]
        self.state.buy_financial += tick["buy_financial"]
        self.state.sell_financial += tick["sell_financial"]

        
        self.state.trades_count += 1

        
        if self.persist_state_every_tick:
            self.repository.save_state(self.state)



    def _update_low_high(
        self,
        low,
        high,
        last
    ):

        if last < low:
            low = last

        if last > high:
            high = last

        return low, high
    
    def _check_brick_close(self, tick, brick_size):

        if self.state is None:
            return "NO_CLOSE", 0

        last_brick = self.last_closed_brick

        if last_brick is None:
            return "NO_CLOSE", 0

        tick_size = self.instrument.tick_size
        brick_distance = self.instrument.get_brick_distance(brick_size)

        last_direction = last_brick["direction"]
        last = self._round_price(tick["last"])
        close = self._round_price(last_brick["close"])

        if last_direction == "UP":

            if last > (close + brick_distance - tick_size):
                qty_bricks = int((last - close) / brick_distance)
                return "CONTINUATION_UP", max(qty_bricks, 1)

            if last < (close - (2 * (brick_distance - tick_size))):
                qty_bricks = int(((close - last) / brick_distance) - 1)
                return "REVERSAL_DOWN", max(qty_bricks, 1)

        elif last_direction == "DOWN":

            if last < (close - brick_distance - tick_size):
                qty_bricks = int((close - last) / brick_distance)
                return "CONTINUATION_DOWN", max(qty_bricks, 1)

            if last > (close + (2 * (brick_distance - tick_size))):
                qty_bricks = int(((last - close) / brick_distance) - 1)
                return "REVERSAL_UP", max(qty_bricks, 1)

        return "NO_CLOSE", 0 


    def _build_closed_brick(self, close_type, close_time):

        if self.state is None:
            return None

        last_brick = self.last_closed_brick

        if last_brick is None:
            return None

        tick_size = self.instrument.tick_size
        brick_distance = self.instrument.get_brick_distance(self.brick_size)
        effective_distance = brick_distance - tick_size

        if close_type == "REVERSAL_UP":
            direction = "UP"
            open_price = self._round_price(float(last_brick["open"]))
            close_price = self._round_price(open_price + effective_distance)

        elif close_type == "REVERSAL_DOWN":
            direction = "DOWN"
            open_price = self._round_price(float(last_brick["open"]))
            close_price = self._round_price(open_price - effective_distance)

        elif close_type == "CONTINUATION_UP":
            direction = "UP"
            open_price = self._round_price(float(last_brick["close"]))
            close_price = self._round_price(open_price + effective_distance)

        elif close_type == "CONTINUATION_DOWN":
            direction = "DOWN"
            open_price = self._round_price(float(last_brick["close"]))
            close_price = self._round_price(open_price - effective_distance)

        else:
            return None

        high_price = self._round_price(
            max(open_price, close_price, self.state.high)
        )

        low_price = self._round_price(
            min(open_price, close_price, self.state.low)
        )

        return {
            "brick_size": self.brick_size,
            "open_time": self.state.open_time,
            "close_time": close_time,
            "open": open_price,
            "close": close_price,
            "high": high_price,
            "low": low_price,
            "direction": direction,
            "volume": self.state.volume,
            "buy_qty": self.state.buy_qty,
            "sell_qty": self.state.sell_qty,
            "buy_financial": self.state.buy_financial,
            "sell_financial": self.state.sell_financial,
            "trades_count": self.state.trades_count,
        }


    def _build_closed_bricks(self, close_type, qty_bricks, tick):

        if self.state is None:
            return None

        bricks = []

        final_close_time = tick["timestamp_ms"]
        step = (final_close_time - self.state.open_time) // qty_bricks

        first_close_time = (
            self.state.open_time + step
            if qty_bricks > 1
            else final_close_time
        )

        first_brick = self._build_closed_brick(
            close_type,
            first_close_time
        )

        if first_brick is None:
            return None

        bricks.append(first_brick)

        tick_size = self.instrument.tick_size
        brick_distance = self.instrument.get_brick_distance(self.brick_size)

        direction = first_brick["direction"]
        open_price = first_brick["close"]

        for i in range(1, qty_bricks):
            open_time = first_brick["open_time"] + (i * step)
            close_time = self.state.open_time + ((i + 1) * step)

            if i == qty_bricks - 1:
                open_time = final_close_time - 1
                close_time = final_close_time

            open_price = self._round_price(open_price)

            if direction == "UP":
                close_price = self._round_price(
                    open_price + brick_distance - tick_size
                )
            else:
                close_price = self._round_price(
                    open_price - (brick_distance - tick_size)
                )

            high_price = self._round_price(
                max(open_price, close_price)
            )

            low_price = self._round_price(
                min(open_price, close_price)
            )

            brick = {
                "brick_size": self.brick_size,
                "open_time": open_time,
                "close_time": close_time,
                "open": open_price,
                "close": close_price,
                "high": high_price,
                "low": low_price,
                "direction": direction,
                "volume": 0,
                "buy_qty": 0,
                "sell_qty": 0,
                "buy_financial": 0,
                "sell_financial": 0,
                "trades_count": 0,
            }

            bricks.append(brick)
            open_price = close_price

        return bricks

    def _reset_state_after_close(self, tick, open_price):
        state = RenkoState()

        state.symbol = self.symbol
        state.brick_size = self.brick_size

        state.open_time = tick["timestamp_ms"]
        state.open = self._round_price(open_price)
        state.last = self._round_price(tick["last"])

        state.high = self._round_price(max(open_price, tick["last"]))
        state.low = self._round_price(min(open_price, tick["last"]))

        state.volume = tick["volume"]
        state.buy_qty = tick["buy_qty"]
        state.sell_qty = tick["sell_qty"]
        state.buy_financial = tick["buy_financial"]
        state.sell_financial = tick["sell_financial"]
        state.trades_count = 1

        state.direction = None

        self.state = state
        self.repository.save_state(state)

        return state

    def _initialize_state(self, tick):
        saved_state = self.repository.get_state(
            self.symbol,
            self.brick_size
        )
        self.last_closed_brick = self.repository.get_last_closed_brick(
            self.symbol,
            self.brick_size
        )

        if saved_state is not None:
            state = RenkoState()

            state.symbol = saved_state["symbol"]
            state.brick_size = saved_state["brick_size"]

            state.open_time = np.datetime64(saved_state["open_time"])
            state.open = self._round_price(saved_state["open"])
            state.last = self._round_price(saved_state["last"])
            state.high = self._round_price(saved_state["high"])
            state.low = self._round_price(saved_state["low"])

            state.direction = saved_state["direction"]

            state.volume = saved_state["volume"]
            state.buy_qty = saved_state["buy_qty"]
            state.sell_qty = saved_state["sell_qty"]
            state.buy_financial = saved_state["buy_financial"]
            state.sell_financial = saved_state["sell_financial"]
            state.trades_count = saved_state["trades_count"]

            self.state = state
            return state

        state = RenkoState()


        if self.last_closed_brick is None:
            open_price = self._round_price(tick["last"])
        else:
            open_price = self._round_price(self.last_closed_brick["close"])

        state.symbol = self.symbol
        state.brick_size = self.brick_size

        state.open_time = tick["timestamp_ms"]
        state.open = open_price
        state.last = self._round_price(tick["last"])

        state.high = self._round_price(max(open_price, tick["last"]))
        state.low = self._round_price(min(open_price, tick["last"]))

        state.volume = tick["volume"]
        state.buy_qty = tick["buy_qty"]
        state.sell_qty = tick["sell_qty"]
        state.buy_financial = tick["buy_financial"]
        state.sell_financial = tick["sell_financial"]
        state.trades_count = 1

        state.direction = None

        self.state = state

        return state

    def _round_price(self, price):
        return self.instrument.round_price(price)

    def flush_state(self):
        if self.state is not None:
            self.repository.save_state(self.state)


