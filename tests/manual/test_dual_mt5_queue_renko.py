import multiprocessing as mp
import time

from ingestion.mt5_realtime_client import MT5RealtimeClient
from services.market_service import MarketService
from services.renko_service import RenkoService


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

ACTIVTRADES_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 - ActivTrades\terminal64.exe"
)

WIN_SYMBOL = "WINV26"
CFD_SYMBOL = "Bra50Oct26"

BRICK_SIZES = (
    10,
    30,
    45,
)

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
                "company": account.get(
                    "company"
                ),
                "server": account.get(
                    "server"
                ),
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


def state_values(state):

    return {
        "open": state.open,
        "last": state.last,
        "high": state.high,
        "low": state.low,
    }


def main():

    print()
    print(
        "TESTE DUAL MT5 -> QUEUE -> RENKO"
    )
    print("=" * 60)


    # ========================================================
    # OBTÉM PREÇOS INICIAIS
    #
    # Fazemos sequencialmente antes de iniciar os workers.
    # ========================================================

    xp_client = MT5RealtimeClient(
        path=XP_MT5_PATH,
    )

    xp_client.connect()

    try:

        raw_win_tick = (
            xp_client.get_tick(
                WIN_SYMBOL
            )
        )

        win_initial_price = float(
            raw_win_tick["last"]
        )

    finally:

        xp_client.disconnect()


    cfd_client = MT5RealtimeClient(
        path=ACTIVTRADES_MT5_PATH,
    )

    cfd_client.connect()

    try:

        raw_cfd_tick = (
            cfd_client.get_tick(
                CFD_SYMBOL
            )
        )

        cfd_initial_price = float(
            raw_cfd_tick["bid"]
        )

    finally:

        cfd_client.disconnect()


    print(
        "WIN preço inicial :",
        win_initial_price,
    )

    print(
        "CFD preço inicial :",
        cfd_initial_price,
    )


    # ========================================================
    # CRIA DOIS RUNTIMES INDEPENDENTES
    # ========================================================

    win_runtime = RenkoService(
        symbol=WIN_SYMBOL,
        brick_sizes=BRICK_SIZES,
    )

    cfd_runtime = RenkoService(
        symbol=WIN_SYMBOL,
        brick_sizes=BRICK_SIZES,
    )


    win_runtime.initialize(
        initial_price=
            win_initial_price
    )

    cfd_runtime.initialize(
        initial_price=
            cfd_initial_price
    )


    # initialize() sozinho não cria state.
    #
    # Usamos o primeiro tick real recebido
    # posteriormente para inicializar o estado
    # caso ele ainda esteja None.


    win_before = {}
    cfd_before = {}


    counts = {
        "WIN": 0,
        "CFD": 0,
    }


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


    finished = set()

    first_win_state_saved = False
    first_cfd_state_saved = False


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


                # ============================================
                # WIN
                # ============================================

                if feed == "WIN":

                    win_runtime.process_tick(
                        tick
                    )

                    if (
                        not
                        first_win_state_saved
                    ):

                        if all(
                            win_runtime.engines[
                                brick_size
                            ].state
                            is not None
                            for brick_size
                            in BRICK_SIZES
                        ):

                            for brick_size in (
                                BRICK_SIZES
                            ):

                                win_before[
                                    brick_size
                                ] = state_values(
                                    win_runtime
                                    .engines[
                                        brick_size
                                    ]
                                    .state
                                )

                            first_win_state_saved = (
                                True
                            )


                # ============================================
                # CFD
                # ============================================

                elif feed == "CFD":

                    cfd_runtime.process_tick(
                        tick
                    )

                    if (
                        not
                        first_cfd_state_saved
                    ):

                        if all(
                            cfd_runtime.engines[
                                brick_size
                            ].state
                            is not None
                            for brick_size
                            in BRICK_SIZES
                        ):

                            for brick_size in (
                                BRICK_SIZES
                            ):

                                cfd_before[
                                    brick_size
                                ] = state_values(
                                    cfd_runtime
                                    .engines[
                                        brick_size
                                    ]
                                    .state
                                )

                            first_cfd_state_saved = (
                                True
                            )


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
                        f"source="
                        f"{tick.source_price}"
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
                    f"worker="
                    f"{message['received_ticks']} | "
                    f"queue="
                    f"{counts[feed]}"
                )


            elif (
                message_type
                ==
                "error"
            ):

                raise RuntimeError(
                    f"Erro worker "
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
    # VALIDAÇÃO FINAL
    # ========================================================

    print()
    print("VALIDAÇÃO RENKO")
    print("=" * 60)


    if counts["WIN"] <= 0:

        raise AssertionError(
            "Nenhum tick WIN recebido."
        )


    if counts["CFD"] <= 0:

        raise AssertionError(
            "Nenhum tick CFD recebido."
        )


    if not first_win_state_saved:

        raise AssertionError(
            "WIN runtime não "
            "inicializou estado."
        )


    if not first_cfd_state_saved:

        raise AssertionError(
            "CFD runtime não "
            "inicializou estado."
        )


    win_any_changed = False
    cfd_any_changed = False


    for brick_size in BRICK_SIZES:

        win_after = state_values(
            win_runtime.engines[
                brick_size
            ].state
        )

        cfd_after = state_values(
            cfd_runtime.engines[
                brick_size
            ].state
        )


        win_changed = (
            win_after
            !=
            win_before[
                brick_size
            ]
        )

        cfd_changed = (
            cfd_after
            !=
            cfd_before[
                brick_size
            ]
        )


        if win_changed:

            win_any_changed = True


        if cfd_changed:

            cfd_any_changed = True


        print()

        print(
            f"{brick_size}R"
        )

        print("-" * 40)

        print(
            "WIN mudou :",
            win_changed,
        )

        print(
            "WIN last  :",
            win_after["last"],
        )

        print(
            "WIN high  :",
            win_after["high"],
        )

        print(
            "WIN low   :",
            win_after["low"],
        )

        print()

        print(
            "CFD mudou :",
            cfd_changed,
        )

        print(
            "CFD last  :",
            cfd_after["last"],
        )

        print(
            "CFD high  :",
            cfd_after["high"],
        )

        print(
            "CFD low   :",
            cfd_after["low"],
        )


    if not win_any_changed:

        raise AssertionError(
            "WIN recebeu ticks, "
            "mas nenhum estado Renko mudou."
        )


    if not cfd_any_changed:

        raise AssertionError(
            "CFD recebeu ticks, "
            "mas nenhum estado Renko mudou."
        )


    print()
    print("=" * 60)

    print(
        "RESULTADO: "
        "DUAL MT5 -> QUEUE -> "
        "DOIS RUNTIMES RENKO OK"
    )


if __name__ == "__main__":

    mp.freeze_support()

    main()