from __future__ import annotations

from typing import Any, Optional

import MetaTrader5 as mt5


class MT5RealtimeClient:
    """
    Cliente MT5 voltado para leitura em tempo real.

    Nesta fase ele é somente leitura:
    - conexão;
    - status do terminal;
    - dados da conta;
    - informações do símbolo;
    - tick atual;
    - posições abertas.

    Nenhum método de envio de ordens será criado ainda.
    """

    def __init__(
        self,
        login: Optional[int] = None,
        server: Optional[str] = None,
        password: Optional[str] = None,
        path: Optional[str] = None,
        timeout_ms: int = 10_000,
    ):
        self.login = login
        self.server = server
        self.password = password
        self.path = path
        self.timeout_ms = timeout_ms
        self.connected = False

    def connect(self) -> None:
        kwargs: dict[str, Any] = {
            "timeout": self.timeout_ms
        }

        if self.login is not None:
            kwargs["login"] = self.login

        if self.server:
            kwargs["server"] = self.server

        if self.password:
            kwargs["password"] = self.password

        if self.path:
            success = mt5.initialize(
                self.path,
                **kwargs
            )
        else:
            success = mt5.initialize(**kwargs)

        if not success:
            self.connected = False

            raise RuntimeError(
                f"Falha ao conectar ao MT5. "
                f"last_error={mt5.last_error()}"
            )

        self.connected = True

    def disconnect(self) -> None:
        mt5.shutdown()
        self.connected = False

    def ensure_connected(self) -> None:
        if not self.connected:
            raise RuntimeError(
                "MT5RealtimeClient não está conectado."
            )

    def get_terminal_info(self) -> Optional[dict[str, Any]]:
        self.ensure_connected()

        info = mt5.terminal_info()

        if info is None:
            return None

        return info._asdict()

    def get_account_info(self) -> Optional[dict[str, Any]]:
        self.ensure_connected()

        info = mt5.account_info()

        if info is None:
            return None

        return info._asdict()

    def ensure_symbol(self, symbol: str) -> None:
        self.ensure_connected()

        info = mt5.symbol_info(symbol)

        if info is None:
            raise ValueError(
                f"Símbolo '{symbol}' não encontrado no MT5."
            )

        if not info.visible:
            success = mt5.symbol_select(
                symbol,
                True
            )

            if not success:
                raise RuntimeError(
                    f"Não foi possível selecionar "
                    f"'{symbol}' no Market Watch. "
                    f"last_error={mt5.last_error()}"
                )

    def get_symbol_info(
        self,
        symbol: str
    ) -> dict[str, Any]:

        self.ensure_symbol(symbol)

        info = mt5.symbol_info(symbol)

        if info is None:
            raise RuntimeError(
                f"symbol_info('{symbol}') retornou None."
            )

        return info._asdict()

    def get_symbol_spec(
        self,
        symbol: str
    ) -> dict[str, Any]:

        info = self.get_symbol_info(symbol)

        keys = (
            "name",
            "description",
            "path",
            "currency_base",
            "currency_profit",
            "currency_margin",
            "digits",
            "point",
            "trade_tick_size",
            "trade_tick_value",
            "trade_tick_value_profit",
            "trade_tick_value_loss",
            "trade_contract_size",
            "volume_min",
            "volume_max",
            "volume_step",
            "trade_stops_level",
            "trade_freeze_level",
            "trade_mode",
            "filling_mode",
            "order_mode",
            "visible",
        )

        return {
            key: info.get(key)
            for key in keys
        }

    def get_tick(
        self,
        symbol: str
    ) -> dict[str, Any]:

        self.ensure_symbol(symbol)

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            raise RuntimeError(
                f"Nenhum tick disponível para "
                f"'{symbol}'. "
                f"last_error={mt5.last_error()}"
            )

        data = tick._asdict()

        bid = data.get("bid")
        ask = data.get("ask")

        if bid is not None and ask is not None:
            data["spread_price"] = ask - bid
        else:
            data["spread_price"] = None

        return data

    def get_positions(
        self,
        symbol: Optional[str] = None
    ) -> list[dict[str, Any]]:

        self.ensure_connected()

        if symbol:
            positions = mt5.positions_get(
                symbol=symbol
            )
        else:
            positions = mt5.positions_get()

        if positions is None:
            raise RuntimeError(
                f"positions_get falhou. "
                f"last_error={mt5.last_error()}"
            )

        return [
            position._asdict()
            for position in positions
        ]

    def send_market_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        deviation: int = 20,
        magic: int = 20260921,
        comment: str = "renko-analysis",
        check_only: bool = True,
    ) -> dict[str, Any]:

        self.ensure_symbol(symbol)

        side = side.upper().strip()

        if side not in (
            "BUY",
            "SELL",
        ):
            raise ValueError(
                "side deve ser BUY ou SELL."
            )

        info = mt5.symbol_info(symbol)

        if info is None:
            raise RuntimeError(
                f"symbol_info('{symbol}') "
                f"retornou None."
            )

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            raise RuntimeError(
                f"symbol_info_tick('{symbol}') "
                f"retornou None. "
                f"last_error={mt5.last_error()}"
            )

        if volume < info.volume_min:
            raise ValueError(
                f"Volume {volume} menor que "
                f"volume_min={info.volume_min}."
            )

        if volume > info.volume_max:
            raise ValueError(
                f"Volume {volume} maior que "
                f"volume_max={info.volume_max}."
            )

        if side == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid

        filling_mode = int(
            info.filling_mode
        )

        if (
            filling_mode & 1
        ):
            order_filling = (
                mt5.ORDER_FILLING_FOK
            )

        elif (
            filling_mode & 2
        ):
            order_filling = (
                mt5.ORDER_FILLING_IOC
            )

        else:
            raise RuntimeError(
                "Nenhum filling mode "
                "suportado para ordem "
                f"a mercado em {symbol}. "
                f"filling_mode="
                f"{filling_mode}"
            )

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": float(price),
            "deviation": deviation,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": order_filling,
        }

        check = mt5.order_check(
            request
        )

        if check is None:
            raise RuntimeError(
                "order_check retornou None. "
                f"last_error={mt5.last_error()}"
            )

        check_data = check._asdict()

        if (
            "request" in check_data
            and hasattr(
                check_data["request"],
                "_asdict",
            )
        ):
            check_data["request"] = (
                check_data["request"]
                ._asdict()
            )

        if check.retcode != 0:
            return {
                "success": False,
                "stage": "check",
                "request": request,
                "check": check_data,
            }

        if check_only:
            return {
                "success": True,
                "stage": "check_only",
                "request": request,
                "check": check_data,
            }

        result = mt5.order_send(
            request
        )

        if result is None:
            raise RuntimeError(
                "order_send retornou None. "
                f"last_error={mt5.last_error()}"
            )

        result_data = result._asdict()

        if (
            "request" in result_data
            and hasattr(
                result_data["request"],
                "_asdict",
            )
        ):
            result_data["request"] = (
                result_data["request"]
                ._asdict()
            )

        success = result.retcode in (
            mt5.TRADE_RETCODE_DONE,
            mt5.TRADE_RETCODE_DONE_PARTIAL,
            mt5.TRADE_RETCODE_PLACED,
        )

        return {
            "success": success,
            "stage": "send",
            "request": request,
            "check": check_data,
            "result": result_data,
        }


    def buy(
        self,
        symbol: str,
        volume: float,
    ) -> dict[str, Any]:

        return self.send_market_order(
            symbol=symbol,
            side="BUY",
            volume=volume,
        )


    def sell(
        self,
        symbol: str,
        volume: float,
    ) -> dict[str, Any]:

        return self.send_market_order(
            symbol=symbol,
            side="SELL",
            volume=volume,
        )

    def close_position(
        self,
        ticket: int,
        deviation: int = 20,
        magic: int = 20260921,
        comment: str = "renko-analysis-close",
        check_only: bool = True,
    ) -> dict[str, Any]:

        self.ensure_connected()

        positions = mt5.positions_get(
            ticket=ticket
        )

        if positions is None:
            raise RuntimeError(
                "positions_get falhou. "
                f"last_error={mt5.last_error()}"
            )

        if len(positions) == 0:
            raise RuntimeError(
                f"Posição {ticket} não encontrada."
            )

        position = positions[0]

        symbol = position.symbol
        volume = position.volume

        self.ensure_symbol(
            symbol
        )

        info = mt5.symbol_info(
            symbol
        )

        if info is None:
            raise RuntimeError(
                f"symbol_info('{symbol}') "
                f"retornou None. "
                f"last_error={mt5.last_error()}"
            )

        tick = mt5.symbol_info_tick(
            symbol
        )

        if tick is None:
            raise RuntimeError(
                f"symbol_info_tick('{symbol}') "
                f"retornou None. "
                f"last_error={mt5.last_error()}"
            )

        # Para fechar uma posição BUY,
        # enviamos uma ordem SELL.
        #
        # Para fechar uma posição SELL,
        # enviamos uma ordem BUY.

        if position.type == mt5.POSITION_TYPE_BUY:

            side = "SELL"
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid

        elif position.type == mt5.POSITION_TYPE_SELL:

            side = "BUY"
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask

        else:

            raise RuntimeError(
                "Tipo de posição MT5 "
                f"não reconhecido: {position.type}"
            )

        filling_mode = int(
            info.filling_mode
        )

        if (
            filling_mode & 1
        ):
            order_filling = (
                mt5.ORDER_FILLING_FOK
            )

        elif (
            filling_mode & 2
        ):
            order_filling = (
                mt5.ORDER_FILLING_IOC
            )

        else:
            raise RuntimeError(
                "Nenhum filling mode "
                "suportado para fechamento "
                f"em {symbol}. "
                f"filling_mode="
                f"{filling_mode}"
            )

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "position": int(ticket),
            "price": float(price),
            "deviation": deviation,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
             "type_filling": order_filling,
        }

        check = mt5.order_check(
            request
        )

        if check is None:
            raise RuntimeError(
                "order_check retornou None. "
                f"last_error={mt5.last_error()}"
            )

        check_data = check._asdict()

        # TradeRequest do MT5 não pode
        # atravessar multiprocessing.Queue.
        if (
            "request" in check_data
            and hasattr(
                check_data["request"],
                "_asdict",
            )
        ):
            check_data["request"] = (
                check_data["request"]
                ._asdict()
            )

        if check.retcode != 0:
            return {
                "success": False,
                "stage": "check",
                "ticket": int(ticket),
                "symbol": symbol,
                "side": side,
                "volume": float(volume),
                "request": request,
                "check": check_data,
            }

        if check_only:
            return {
                "success": True,
                "stage": "check_only",
                "ticket": int(ticket),
                "symbol": symbol,
                "side": side,
                "volume": float(volume),
                "request": request,
                "check": check_data,
            }

        result = mt5.order_send(
            request
        )

        if result is None:
            raise RuntimeError(
                "order_send retornou None. "
                f"last_error={mt5.last_error()}"
            )

        result_data = result._asdict()

        # Mesma conversão necessária
        # no resultado do order_send.
        if (
            "request" in result_data
            and hasattr(
                result_data["request"],
                "_asdict",
            )
        ):
            result_data["request"] = (
                result_data["request"]
                ._asdict()
            )

        success = result.retcode in (
            mt5.TRADE_RETCODE_DONE,
            mt5.TRADE_RETCODE_DONE_PARTIAL,
            mt5.TRADE_RETCODE_PLACED,
        )

        return {
            "success": success,
            "stage": "send",
            "ticket": int(ticket),
            "symbol": symbol,
            "side": side,
            "volume": float(volume),
            "request": request,
            "check": check_data,
            "result": result_data,
        }
    
    def find_symbols(self, text: str) -> list[dict]:
        self.ensure_connected()

        symbols = mt5.symbols_get()

        if symbols is None:
            raise RuntimeError(
                f"symbols_get falhou. last_error={mt5.last_error()}"
            )

        text = text.lower()

        results = []

        for symbol in symbols:
            name = symbol.name.lower()
            description = (symbol.description or "").lower()

            if text in name or text in description:
                results.append(
                    {
                        "name": symbol.name,
                        "description": symbol.description,
                        "path": symbol.path,
                        "visible": symbol.visible,
                    }
                )

        return results
