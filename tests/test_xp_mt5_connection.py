import MetaTrader5 as mt5


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

SYMBOL = "WINV26"


def main():
    print("Conectando ao MT5 da XP...")

    if not mt5.initialize(
        path=XP_MT5_PATH
    ):
        print(
            "Falha ao conectar:",
            mt5.last_error()
        )
        return

    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()

        print("\nTERMINAL")
        print("=" * 40)

        if terminal is not None:
            print(
                "connected:",
                terminal.connected
            )
            print(
                "company:",
                terminal.company
            )
            print(
                "name:",
                terminal.name
            )

        print("\nCONTA")
        print("=" * 40)

        if account is not None:
            print(
                "login:",
                account.login
            )
            print(
                "server:",
                account.server
            )
            print(
                "company:",
                account.company
            )

        print("\nSÍMBOLO")
        print("=" * 40)

        info = mt5.symbol_info(
            SYMBOL
        )

        if info is None:
            print(
                f"{SYMBOL} não encontrado."
            )
            print(
                "Erro:",
                mt5.last_error()
            )
            return

        if not info.visible:
            mt5.symbol_select(
                SYMBOL,
                True
            )

        print(
            "symbol:",
            info.name
        )
        print(
            "visible:",
            info.visible
        )
        print(
            "digits:",
            info.digits
        )
        print(
            "point:",
            info.point
        )
        print(
            "trade_tick_size:",
            info.trade_tick_size
        )

        tick = mt5.symbol_info_tick(
            SYMBOL
        )

        print("\nÚLTIMO TICK")
        print("=" * 40)

        if tick is None:
            print(
                "Nenhum tick retornado."
            )
        else:
            print(
                "time_msc:",
                tick.time_msc
            )
            print(
                "bid:",
                tick.bid
            )
            print(
                "ask:",
                tick.ask
            )
            print(
                "last:",
                tick.last
            )
            print(
                "volume:",
                tick.volume
            )
            print(
                "volume_real:",
                tick.volume_real
            )

    finally:
        mt5.shutdown()
        print(
            "\nMT5 XP desconectado."
        )


if __name__ == "__main__":
    main()