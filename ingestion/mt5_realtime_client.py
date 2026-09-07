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
