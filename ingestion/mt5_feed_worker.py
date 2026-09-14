import time

from ingestion.mt5_realtime_client import (
    MT5RealtimeClient,
)

from services.market_service import (
    MarketService,
)


def run_mt5_feed_worker(
    feed_name: str,
    terminal_path: str,
    symbol: str,
    output_queue,
    poll_interval: float = 0.02,
):
    """
    Worker dedicado a um terminal MT5.

    Responsabilidades:

    1. conectar ao terminal MT5 informado;
    2. criar o MarketService;
    3. receber RealtimeTick;
    4. enviar os ticks ao processo principal
       através da multiprocessing.Queue.

    Este worker NÃO processa Renko.
    O Renko permanece no processo principal.
    """

    mt5_client = MT5RealtimeClient(
        path=terminal_path,
    )

    market_service = None

    try:

        mt5_client.connect()

        terminal_info = (
            mt5_client.get_terminal_info()
        )

        print("")
        print(
            f"{feed_name} CONECTADO"
        )

        print(
            f"company : "
            f"{terminal_info.get('company')}"
        )

        print(
            f"server  : "
            f"{terminal_info.get('server')}"
        )


        market_service = MarketService(
            mt5_client=mt5_client,
            symbol=symbol,
            poll_interval=poll_interval,
        )


        def on_tick(tick):

            output_queue.put(
                {
                    "type": "tick",
                    "feed": feed_name,
                    "tick": tick,
                }
            )


        market_service.subscribe(
            on_tick
        )


        market_service.start()


        # Mantém o processo vivo.
        #
        # O encerramento normal será feito
        # pelo processo principal através de
        # process.terminate() nesta primeira
        # versão da integração.
        #
        # Posteriormente podemos trocar isso
        # por um Event de shutdown se quisermos
        # encerramento cooperativo.

        while True:
            time.sleep(
                0.25
            )


    except KeyboardInterrupt:

        pass


    except Exception as exc:

        output_queue.put(
            {
                "type": "error",
                "feed": feed_name,
                "error": str(exc),
            }
        )


    finally:

        if market_service is not None:

            try:
                market_service.stop()
            except Exception:
                pass


        try:
            mt5_client.disconnect()
        except Exception:
            pass