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
    command_queue=None,
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

        while True:

            if command_queue is not None:

                try:

                    command = (
                        command_queue
                        .get_nowait()
                    )

                except Exception:

                    command = None

                if command is not None:

                    command_type = (
                        command.get(
                            "type"
                        )
                    )

                    # -------------------------
                    # CONSULTA DE POSIÇÕES
                    # -------------------------

                    if (
                        command_type
                        == "get_positions"
                    ):

                        request_id = (
                            command.get(
                                "request_id"
                            )
                        )

                        try:

                            positions = (
                                mt5_client
                                .get_positions(
                                    symbol=(
                                        command.get(
                                            "symbol"
                                        )
                                    )
                                )
                            )

                            output_queue.put(
                                {
                                    "type":
                                        "positions_result",

                                    "feed":
                                        feed_name,

                                    "request_id":
                                        request_id,

                                    "positions":
                                        positions,
                                }
                            )

                        except Exception as exc:

                            output_queue.put(
                                {
                                    "type":
                                        "positions_result",

                                    "feed":
                                        feed_name,

                                    "request_id":
                                        request_id,

                                    "error":
                                        str(exc),
                                }
                            )

                        continue

                    # -------------------------
                    # FECHAMENTO DE POSIÇÃO
                    # -------------------------

                    if (
                        command_type
                        == "close_position"
                    ):

                        request_id = (
                            command.get(
                                "request_id"
                            )
                        )

                        try:

                            expected_feed = (
                                command.get(
                                    "expected_feed"
                                )
                            )

                            expected_symbol = (
                                command.get(
                                    "expected_symbol"
                                )
                            )

                            worker_feed = (
                                feed_name
                                .strip()
                                .upper()
                            )

                            worker_symbol = symbol

                            worker_company = (
                                terminal_info.get(
                                    "company"
                                )
                            )

                            expected_company = {
                                "WIN":
                                    "XP Investimentos CCTVM S/A",

                                "CFD":
                                    "ActivTrades Corp",
                            }.get(
                                worker_feed
                            )

                            if expected_company is None:
                                raise RuntimeError(
                                    "FECHAMENTO BLOQUEADO: "
                                    f"worker desconhecido="
                                    f"{worker_feed}."
                                )

                            if (
                                expected_feed
                                != worker_feed
                            ):
                                raise RuntimeError(
                                    "FECHAMENTO BLOQUEADO: "
                                    f"feed esperado="
                                    f"{expected_feed}, "
                                    f"worker="
                                    f"{worker_feed}."
                                )

                            if (
                                expected_symbol
                                != worker_symbol
                            ):
                                raise RuntimeError(
                                    "FECHAMENTO BLOQUEADO: "
                                    f"symbol esperado="
                                    f"{expected_symbol}, "
                                    f"worker="
                                    f"{worker_symbol}."
                                )

                            if (
                                worker_company
                                != expected_company
                            ):
                                raise RuntimeError(
                                    "FECHAMENTO BLOQUEADO: "
                                    f"corretora esperada="
                                    f"{expected_company}, "
                                    f"terminal conectado="
                                    f"{worker_company}."
                                )

                            result = (
                                mt5_client
                                .close_position(
                                    ticket=command.get(
                                        "ticket"
                                    ),
                                    check_only=command.get(
                                        "check_only",
                                        True,
                                    ),
                                )
                            )

                            output_queue.put(
                                {
                                    "type":
                                        "close_position_result",

                                    "feed":
                                        feed_name,

                                    "request_id":
                                        request_id,

                                    "result":
                                        result,
                                }
                            )

                        except Exception as exc:

                            output_queue.put(
                                {
                                    "type":
                                        "close_position_result",

                                    "feed":
                                        feed_name,

                                    "request_id":
                                        request_id,

                                    "error":
                                        str(exc),
                                }
                            )

                        continue
                    # -------------------------
                    # ORDEM A MERCADO
                    # -------------------------

                    if (
                        command_type
                        == "market_order"
                    ):

                        request_id = (
                            command.get(
                                "request_id"
                            )
                        )

                        try:

                            expected_feed = (
                                command.get(
                                    "expected_feed"
                                )
                            )

                            expected_symbol = (
                                command.get(
                                    "expected_symbol"
                                )
                            )

                            worker_feed = (
                                feed_name
                                .strip()
                                .upper()
                            )

                            worker_symbol = symbol

                            worker_company = (
                                terminal_info.get(
                                    "company"
                                )
                            )

                            expected_company = {
                                "WIN":
                                    "XP Investimentos CCTVM S/A",

                                "CFD":
                                    "ActivTrades Corp",
                            }.get(
                                worker_feed
                            )

                            if expected_company is None:
                                raise RuntimeError(
                                    "ORDEM BLOQUEADA: "
                                    f"worker desconhecido="
                                    f"{worker_feed}."
                                )

                            if (
                                expected_feed
                                != worker_feed
                            ):
                                raise RuntimeError(
                                    "ORDEM BLOQUEADA: "
                                    f"feed esperado="
                                    f"{expected_feed}, "
                                    f"worker="
                                    f"{worker_feed}."
                                )

                            if (
                                expected_symbol
                                != worker_symbol
                            ):
                                raise RuntimeError(
                                    "ORDEM BLOQUEADA: "
                                    f"symbol esperado="
                                    f"{expected_symbol}, "
                                    f"worker="
                                    f"{worker_symbol}."
                                )

                            if (
                                worker_company
                                != expected_company
                            ):
                                raise RuntimeError(
                                    "ORDEM BLOQUEADA: "
                                    f"corretora esperada="
                                    f"{expected_company}, "
                                    f"terminal conectado="
                                    f"{worker_company}."
                                )

                            result = (
                                mt5_client
                                .send_market_order(
                                    symbol=(
                                        command.get(
                                            "symbol"
                                        )
                                    ),
                                    side=(
                                        command.get(
                                            "side"
                                        )
                                    ),
                                    volume=(
                                        command.get(
                                            "volume"
                                        )
                                    ),
                                    check_only=(
                                        command.get(
                                            "check_only",
                                            True,
                                        )
                                    ),
                                )
                            )

                            output_queue.put(
                                {
                                    "type":
                                        "order_result",

                                    "feed":
                                        feed_name,

                                    "request_id":
                                        request_id,

                                    "result":
                                        result,
                                }
                            )

                        except Exception as exc:

                            output_queue.put(
                                {
                                    "type":
                                        "order_result",

                                    "feed":
                                        feed_name,

                                    "request_id":
                                        request_id,

                                    "error":
                                        str(exc),
                                }
                            )

            time.sleep(
                0.05
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