import multiprocessing as mp
import time

from ingestion.mt5_realtime_client import MT5RealtimeClient
from services.market_service import MarketService


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

ACTIVTRADES_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 - ActivTrades\terminal64.exe"
)

WIN_SYMBOL = "WINV26"
CFD_SYMBOL = "Bra50Oct26"

TEST_SECONDS = 15


def feed_worker(
    terminal_path: str,
    symbol: str,
    feed_name: str,
    output_queue,
):

    client = MT5RealtimeClient(
        path=terminal_path,
    )

    client.connect()

    try:

        account = client.get_account_info()

        output_queue.put(
            {
                "type": "connected",
                "feed": feed_name,
                "company": account.get("company"),
                "server": account.get("server"),
            }
        )

        service = MarketService(
            mt5_client=client,
            symbol=symbol,
            poll_interval=0.02,
        )

        def send_tick(tick):

            output_queue.put(
                {
                    "type": "tick",
                    "feed": feed_name,
                    "tick": tick,
                }
            )

        service.subscribe(
            send_tick
        )

        service.start()

        try:

            time.sleep(
                TEST_SECONDS
            )

        finally:

            service.stop()

        output_queue.put(
            {
                "type": "finished",
                "feed": feed_name,
                "received_ticks":
                    service.received_ticks,
            }
        )

    except Exception as exc:

        output_queue.put(
            {
                "type": "error",
                "feed": feed_name,
                "error": repr(exc),
            }
        )

    finally:

        client.disconnect()


def main():

    print()
    print("TESTE DUAL MT5 -> QUEUE")
    print("=" * 60)

    ctx = mp.get_context(
        "spawn"
    )

    output_queue = ctx.Queue()

    xp_process = ctx.Process(
        target=feed_worker,
        args=(
            XP_MT5_PATH,
            WIN_SYMBOL,
            "WIN",
            output_queue,
        ),
    )

    cfd_process = ctx.Process(
        target=feed_worker,
        args=(
            ACTIVTRADES_MT5_PATH,
            CFD_SYMBOL,
            "CFD",
            output_queue,
        ),
    )

    xp_process.start()
    cfd_process.start()

    counts = {
        "WIN": 0,
        "CFD": 0,
    }

    latest = {
        "WIN": None,
        "CFD": None,
    }

    finished = set()

    try:

        while len(finished) < 2:

            message = output_queue.get(
                timeout=30
            )

            message_type = (
                message["type"]
            )

            feed = (
                message["feed"]
            )

            if (
                message_type
                ==
                "connected"
            ):

                print()

                print(
                    f"{feed} CONECTADO"
                )

                print(
                    "company :",
                    message["company"],
                )

                print(
                    "server  :",
                    message["server"],
                )

            elif (
                message_type
                ==
                "tick"
            ):

                tick = (
                    message["tick"]
                )

                counts[feed] += 1
                latest[feed] = tick

                # Imprime somente a cada
                # 50 ticks do WIN e
                # 5 ticks do CFD.

                interval = (
                    50
                    if feed == "WIN"
                    else 5
                )

                if (
                    counts[feed]
                    % interval
                    ==
                    0
                ):

                    print(
                        f"{feed} | "
                        f"ticks={counts[feed]} | "
                        f"price={tick.price} | "
                        f"source={tick.source_price}"
                    )

            elif (
                message_type
                ==
                "finished"
            ):

                finished.add(
                    feed
                )

                print()

                print(
                    f"{feed} FINALIZADO | "
                    f"ticks worker="
                    f"{message['received_ticks']} | "
                    f"ticks queue="
                    f"{counts[feed]}"
                )

            elif (
                message_type
                ==
                "error"
            ):

                raise RuntimeError(
                    f"Erro no worker "
                    f"{feed}: "
                    f"{message['error']}"
                )

    finally:

        xp_process.join(
            timeout=5
        )

        cfd_process.join(
            timeout=5
        )

        if xp_process.is_alive():

            xp_process.terminate()
            xp_process.join()

        if cfd_process.is_alive():

            cfd_process.terminate()
            cfd_process.join()


    # ========================================================
    # VALIDAÇÃO
    # ========================================================

    print()
    print("VALIDAÇÃO")
    print("=" * 60)

    print(
        "WIN ticks :",
        counts["WIN"],
    )

    print(
        "CFD ticks :",
        counts["CFD"],
    )


    if counts["WIN"] <= 0:

        raise AssertionError(
            "Nenhum tick WIN chegou "
            "ao processo principal."
        )


    if counts["CFD"] <= 0:

        raise AssertionError(
            "Nenhum tick CFD chegou "
            "ao processo principal."
        )


    win_tick = latest["WIN"]
    cfd_tick = latest["CFD"]


    print()

    print(
        "WIN último preço :",
        win_tick.price,
    )

    print(
        "WIN LAST         :",
        win_tick.last,
    )

    print(
        "WIN source       :",
        win_tick.source_price,
    )


    print()

    print(
        "CFD último preço :",
        cfd_tick.price,
    )

    print(
        "CFD BID          :",
        cfd_tick.bid,
    )

    print(
        "CFD LAST         :",
        cfd_tick.last,
    )

    print(
        "CFD source       :",
        cfd_tick.source_price,
    )


    if (
        win_tick.source_price
        !=
        "last"
    ):

        raise AssertionError(
            "WIN recebido pela Queue "
            "não está usando LAST."
        )


    if (
        cfd_tick.source_price
        !=
        "bid"
    ):

        raise AssertionError(
            "CFD recebido pela Queue "
            "não está usando BID."
        )


    if (
        cfd_tick.price
        !=
        cfd_tick.bid
    ):

        raise AssertionError(
            "Preço CFD recebido pela "
            "Queue é diferente do BID."
        )


    print()
    print("=" * 60)

    print(
        "RESULTADO: "
        "DUAL MT5 -> QUEUE OK"
    )

    print(
        "WIN E CFD CHEGARAM "
        "SIMULTANEAMENTE AO "
        "PROCESSO PRINCIPAL"
    )


if __name__ == "__main__":

    mp.freeze_support()

    main()