

import multiprocessing as mp
import queue
import threading
import time

from ingestion.mt5_feed_worker import (
    run_mt5_feed_worker,
)


class DualMT5FeedService:
    """
    Gerencia dois feeds MT5 em processos independentes:

    WIN:
        XP -> WINV26 -> LAST

    CFD:
        ActivTrades -> Bra50Oct26 -> BID

    Os workers apenas coletam RealtimeTick.
    O processamento de Renko continua no processo principal.
    """

    def __init__(
        self,
        win_terminal_path: str,
        win_symbol: str,
        cfd_terminal_path: str,
        cfd_symbol: str,
        poll_interval: float = 0.02,
    ):
        self.win_terminal_path = win_terminal_path
        self.win_symbol = win_symbol

        self.cfd_terminal_path = cfd_terminal_path
        self.cfd_symbol = cfd_symbol

        self.poll_interval = poll_interval

        self._context = mp.get_context("spawn")

        self._queue = None
        self._win_command_queue = None
        self._cfd_command_queue = None

        self._win_process = None
        self._cfd_process = None

        self._consumer_thread = None

        self._running = False

        self._win_callback = None
        self._cfd_callback = None

        self.win_received_ticks = 0
        self.cfd_received_ticks = 0

        self.latest_win_tick = None
        self.latest_cfd_tick = None

        self._command_results = {}
        self._command_results_lock = (
            threading.Lock()
        )

    # ========================================================
    # CALLBACKS
    # ========================================================

    def set_win_callback(
        self,
        callback,
    ) -> None:

        self._win_callback = callback


    def set_cfd_callback(
        self,
        callback,
    ) -> None:

        self._cfd_callback = callback


    # ========================================================
    # START
    # ========================================================

    def start(self) -> None:

        if self._running:
            return

        # Impede nova inicialização com recursos anteriores ativos.
        for process in (
            self._win_process,
            self._cfd_process,
        ):
            if (
                process is not None
                and process.pid is not None
                and process.is_alive()
            ):
                raise RuntimeError(
                    "Não é possível iniciar o DualMT5FeedService: "
                    f"worker anterior pid={process.pid} ainda ativo."
                )

        if (
            self._consumer_thread is not None
            and self._consumer_thread.is_alive()
        ):
            raise RuntimeError(
                "Não é possível iniciar o DualMT5FeedService: "
                "thread consumidora anterior ainda ativa."
        )

        # ========================================================
        # 1. INICIALIZA AS FILAS
        # ========================================================

        try:
            self._queue = self._context.Queue()

            self._win_command_queue = self._context.Queue()

            self._cfd_command_queue = self._context.Queue()

            # ----------------------------------------------------
            # Reinicia os dados da sessão.
            # ----------------------------------------------------

            self.win_received_ticks = 0
            self.cfd_received_ticks = 0

            self.latest_win_tick = None
            self.latest_cfd_tick = None

            # Permite que o stop() limpe recursos mesmo
            # se a inicialização falhar parcialmente.
            self._running = True

            # ====================================================
            # 2. CRIA O WORKER XP / WIN
            # ====================================================

            self._win_process = self._context.Process(
                target=run_mt5_feed_worker,
                kwargs={
                    "feed_name": "WIN",
                    "terminal_path": self.win_terminal_path,
                    "symbol": self.win_symbol,
                    "output_queue": self._queue,
                    "command_queue": self._win_command_queue,
                    "poll_interval": self.poll_interval,
                },
                name="mt5-win-feed",
            )

            # ====================================================
            # 3. CRIA O WORKER ACTIVTRADES / CFD
            # ====================================================

            self._cfd_process = self._context.Process(
                target=run_mt5_feed_worker,
                kwargs={
                    "feed_name": "CFD",
                    "terminal_path": self.cfd_terminal_path,
                    "symbol": self.cfd_symbol,
                    "output_queue": self._queue,
                    "command_queue": self._cfd_command_queue,
                    "poll_interval": self.poll_interval,
                },
                name="mt5-cfd-feed",
            )

            # ====================================================
            # 4. CRIA A THREAD CONSUMIDORA
            # ====================================================

            # A thread executa no processo principal.
            # Assim, os callbacks continuam acessando os
            # RenkoService utilizados pela API.

            self._consumer_thread = threading.Thread(
                target=self._consume_queue,
                name="dual-mt5-queue-consumer",
                daemon=True,
            )

            # ====================================================
            # 5. INICIA OS WORKERS
            # ====================================================

            self._win_process.start()

            print(
                f"[DualMT5] WIN worker "
                f"pid={self._win_process.pid} "
                f"alive={self._win_process.is_alive()}",
                flush=True,
            )

            self._cfd_process.start()

            print(
                f"[DualMT5] CFD worker "
                f"pid={self._cfd_process.pid} "
                f"alive={self._cfd_process.is_alive()}",
                flush=True,
            )

            # ====================================================
            # 6. INICIA A THREAD CONSUMIDORA
            # ====================================================

            self._consumer_thread.start()

            print(
                "[DualMT5] Feed iniciado com sucesso.",
                flush=True,
            )

        # ========================================================
        # 7. TRATA FALHAS NA INICIALIZAÇÃO
        # ========================================================

        except Exception:

            print(
                "[DualMT5] Falha durante a inicialização. "
                "Executando limpeza dos recursos.",
                flush=True,
            )

            # Se a falha aconteceu antes de _running=True,
            # habilitamos a tentativa de limpeza das filas
            # que eventualmente tenham sido criadas.
            self._running = True

            try:
                self.stop()

            except Exception as cleanup_error:

                print(
                    "[DualMT5] Erro adicional durante "
                    f"a limpeza: {cleanup_error}",
                    flush=True,
                )

            # Preserva a exceção original de start().
            raise


    # ========================================================
    # CONSUMIDOR
    # ========================================================

    def _consume_queue(self) -> None:

        while self._running:

            try:

                message = self._queue.get(
                    timeout=0.25
                )

            except queue.Empty:

                continue

            except Exception as exc:

                if self._running:
                    print(
                        "Erro ao consumir Queue MT5: "
                        f"{exc}"
                    )

                continue


            message_type = (
                message.get("type")
            )


            # ------------------------------------------------
            # ERRO DO WORKER
            # ------------------------------------------------

            if message_type == "error":

                print("")
                print(
                    "ERRO NO WORKER MT5"
                )

                print(
                    f"feed  : "
                    f"{message.get('feed')}"
                )

                print(
                    f"erro  : "
                    f"{message.get('error')}"
                )

                continue

            # ------------------------------------------------
            # RESULTADO DE ORDEM
            # ------------------------------------------------

            if message_type == "order_result":

                request_id = message.get(
                    "request_id"
                )

                # Guarda o resultado para que
                # a API possa recuperá-lo.
                if request_id is not None:

                    with self._command_results_lock:

                        self._command_results[
                            request_id
                        ] = message

                print("")
                feed = (
                    message.get("feed")
                    or "UNKNOWN"
                )

                print(
                    f"[{feed} ORDER RESULT]"
                )

                print(
                    f"request_id : "
                    f"{request_id}"
                )

                if message.get("error"):

                    print(
                        f"error      : "
                        f"{message.get('error')}"
                    )

                else:

                    print(
                        f"result     : "
                        f"{message.get('result')}"
                    )

                continue


            # ------------------------------------------------
            # POSIÇÕES DA XP
            # ------------------------------------------------

            if message_type == "positions_result":

                request_id = message.get(
                    "request_id"
                )

                if request_id is not None:

                    with self._command_results_lock:

                        self._command_results[
                            request_id
                        ] = message

                print("")
                feed = (
                    message.get("feed")
                    or "UNKNOWN"
                )

                print(
                    f"[{feed} POSITIONS RESULT]"
                )

                print(
                    f"request_id : "
                    f"{message.get('request_id')}"
                )

                if message.get("error"):

                    print(
                        f"error      : "
                        f"{message.get('error')}"
                    )

                else:

                    print(
                        f"positions  : "
                        f"{message.get('positions')}"
                    )

                continue

            # ------------------------------------------------
            # RESULTADO DO FECHAMENTO DE POSIÇÃO
            # ------------------------------------------------

            if message_type == "close_position_result":

                request_id = message.get(
                    "request_id"
                )

                if request_id is not None:

                    with self._command_results_lock:

                        self._command_results[
                            request_id
                        ] = message

                print("")
                print("")

                feed = (
                    message.get("feed")
                    or "UNKNOWN"
                )

                print(
                    f"[{feed} CLOSE POSITION RESULT]"
                )

                print(
                    f"request_id : "
                    f"{message.get('request_id')}"
                )

                if message.get("error"):

                    print(
                        f"error      : "
                        f"{message.get('error')}"
                    )

                else:

                    print(
                        f"result     : "
                        f"{message.get('result')}"
                    )

                continue
            # ------------------------------------------------
            # TICK
            # ------------------------------------------------

            if message_type != "tick":
                continue


            feed = message.get(
                "feed"
            )

            tick = message.get(
                "tick"
            )


            if tick is None:
                continue


            # ------------------------------------------------
            # WIN
            # ------------------------------------------------

            if feed == "WIN":

                self.win_received_ticks += 1

                self.latest_win_tick = tick

                if (
                    self._win_callback
                    is not None
                ):

                    try:

                        self._win_callback(
                            tick
                        )

                    except Exception as exc:

                        print(
                            "Erro no callback WIN: "
                            f"{exc}"
                        )


            # ------------------------------------------------
            # CFD
            # ------------------------------------------------

            elif feed == "CFD":

                self.cfd_received_ticks += 1

                self.latest_cfd_tick = tick

                if (
                    self._cfd_callback
                    is not None
                ):

                    try:

                        self._cfd_callback(
                            tick
                        )

                    except Exception as exc:

                        print(
                            "Erro no callback CFD: "
                            f"{exc}"
                        )


    # ========================================================
    # GETTERS
    # ========================================================

    @property
    def running(self) -> bool:

        return self._running


    def get_latest_win_tick(self):

        return self.latest_win_tick


    def get_latest_cfd_tick(self):

        return self.latest_cfd_tick

    def _get_trading_route(
        self,
        feed: str,
    ):

        feed = (
            feed
            .strip()
            .upper()
        )

        if feed == "WIN":
            return {
                "command_queue":
                    self._win_command_queue,
                "symbol":
                    self.win_symbol,
            }

        if feed == "CFD":
            return {
                "command_queue":
                    self._cfd_command_queue,
                "symbol":
                    self.cfd_symbol,
            }

        raise ValueError(
            f"Feed de trading desconhecido: {feed}"
        )

    # ========================================================
    # TRADING
    # ========================================================

    def send_market_order(
        self,
        side: str,
        volume: float = 1,
        check_only: bool = True,
        feed: str = "WIN",
    ) -> str:

        if not self._running:
            raise RuntimeError(
                "DualMT5FeedService não está rodando."
            )

        route = self._get_trading_route(
            feed
        )

        command_queue = (
            route["command_queue"]
        )

        symbol = (
            route["symbol"]
        )

        if command_queue is None:
            raise RuntimeError(
                f"Fila de comandos {feed} "
                f"não está disponível."
            )

        import uuid

        request_id = str(
            uuid.uuid4()
        )

        command_queue.put(
            {
                "type": "market_order",
                "request_id": request_id,

                # Identidade esperada da rota.
                # O worker deverá validar estes dados
                # antes de permitir qualquer ordem.
                "expected_feed": feed.strip().upper(),
                "expected_symbol": symbol,

                "symbol": symbol,
                "side": side,
                "volume": volume,
                "check_only": check_only,
            }
        )

        return request_id


    def get_positions(
        self,
        feed: str = "WIN",
    ) -> str:

        if not self._running:
            raise RuntimeError(
                "DualMT5FeedService não está rodando."
            )

        route = self._get_trading_route(
            feed
        )

        command_queue = (
            route["command_queue"]
        )

        symbol = (
            route["symbol"]
        )

        if command_queue is None:
            raise RuntimeError(
                f"Fila de comandos {feed} "
                f"não está disponível."
            )

        import uuid

        request_id = str(
            uuid.uuid4()
        )

        command_queue.put(
            {
                "type": "get_positions",
                "request_id": request_id,
                "symbol": symbol,
            }
        )

        return request_id


    def close_position(
        self,
        ticket: int,
        volume: float | None = None,
        check_only: bool = True,
        feed: str = "WIN",
    ) -> str:

        if not self._running:
            raise RuntimeError(
                "DualMT5FeedService não está rodando."
            )

        route = self._get_trading_route(
            feed
        )

        command_queue = (
            route["command_queue"]
        )

        symbol = (
            route["symbol"]
        )

        if command_queue is None:
            raise RuntimeError(
                f"Fila de comandos {feed} "
                f"não está disponível."
            )

        import uuid

        request_id = str(
            uuid.uuid4()
        )

        command_queue.put(
            {
                "type": "close_position",
                "request_id": request_id,

                # Identidade esperada da rota.
                # O worker deverá validar estes dados
                # antes de permitir o fechamento.
                "expected_feed":
                    feed.strip().upper(),

                "expected_symbol":
                    symbol,

                "ticket":
                    int(ticket),

                "volume":
                    (
                        float(volume)
                        if volume is not None
                        else None
                    ),

                "check_only":
                    check_only,
            }
        )

        return request_id


    

    def send_win_market_order(
        self,
        side: str,
        volume: float = 1,
        check_only: bool = True,
    ) -> str:

        if not self._running:
            raise RuntimeError(
                "DualMT5FeedService não está rodando."
            )

        if self._win_command_queue is None:
            raise RuntimeError(
                "Fila de comandos WIN não está disponível."
            )

        import uuid

        request_id = str(
            uuid.uuid4()
        )

        self._win_command_queue.put(
            {
                "type": "market_order",
                "request_id": request_id,
                "symbol": self.win_symbol,
                "side": side,
                "volume": volume,
                "check_only": check_only,
            }
        )

        return request_id

    def get_win_positions(
        self,
    ) -> str:

        if not self._running:
            raise RuntimeError(
                "DualMT5FeedService não está rodando."
            )

        if self._win_command_queue is None:
            raise RuntimeError(
                "Fila de comandos WIN não está disponível."
            )

        import uuid

        request_id = str(
            uuid.uuid4()
        )

        self._win_command_queue.put(
            {
                "type": "get_positions",
                "request_id": request_id,
                "symbol": self.win_symbol,
            }
        )

        return request_id

    def close_win_position(
        self,
        ticket: int,
        check_only: bool = True,
    ) -> str:

        if not self._running:
            raise RuntimeError(
                "DualMT5FeedService não está rodando."
            )

        if self._win_command_queue is None:
            raise RuntimeError(
                "Fila de comandos WIN não está disponível."
            )

        import uuid

        request_id = str(
            uuid.uuid4()
        )

        self._win_command_queue.put(
            {
                "type": "close_position",
                "request_id": request_id,
                "ticket": int(ticket),
                "check_only": check_only,
            }
        )

        return request_id

    def wait_for_command_result(
        self,
        request_id: str,
        timeout: float = 3.0,
    ):

        deadline = (
            time.monotonic()
            + timeout
        )

        while time.monotonic() < deadline:

            with self._command_results_lock:

                message = (
                    self._command_results
                    .pop(
                        request_id,
                        None,
                    )
                )

            if message is not None:
                return message

            time.sleep(
                0.01
            )

        return None
    # ========================================================
    # STOP
    # ========================================================

    def stop(self) -> None:

        print(
            "[DualMT5] STOP 1 - iniciado",
            flush=True,
        )

        if (
            not self._running
            and self._win_process is None
            and self._cfd_process is None
            and self._consumer_thread is None
            and self._queue is None
            and self._win_command_queue is None
            and self._cfd_command_queue is None
        ):
            print(
                "[DualMT5] STOP - já estava parado",
                flush=True,
            )
            return

        self._running = False
        shutdown_errors = []

        # ========================================================
        # 1. ENCERRA OS WORKERS
        # ========================================================

        for process in (
            self._win_process,
            self._cfd_process,
        ):
            if process is None:
                continue

            # Processo criado, mas nunca iniciado.
            if process.pid is None:
                print(
                    "[DualMT5] worker não iniciado; "
                    "ignorando terminate/join",
                    flush=True,
                )
                continue

            print(
                f"[DualMT5] encerrando worker pid={process.pid}",
                flush=True,
            )

            if process.is_alive():
                process.terminate()

            process.join(timeout=5)

            # Se o worker resistiu ao terminate, força o encerramento.
            if process.is_alive():
                print(
                    f"[DualMT5] worker pid={process.pid} "
                    "não encerrou; executando kill()",
                    flush=True,
                )

                process.kill()
                process.join(timeout=5)

                if process.is_alive():
                    shutdown_errors.append(
                        f"Worker MT5 pid={process.pid} "
                        "permanece ativo após kill()."
                    )

            print(
                f"[DualMT5] worker pid={process.pid} encerrado",
                flush=True,
            )

        print(
            "[DualMT5] STOP 2 - workers tratados",
            flush=True,
        )

        # ========================================================
        # 2. AGUARDA A THREAD CONSUMIDORA
        # ========================================================

        if (
            self._consumer_thread is not None
            and self._consumer_thread.ident is not None
        ):

            print(
                "[DualMT5] aguardando consumer",
                flush=True,
            )

            self._consumer_thread.join(timeout=2)

            if self._consumer_thread.is_alive():
                shutdown_errors.append(
                    "Thread consumidora permanece ativa "
                    "após timeout de 2 segundos."
                )

            print(
                f"[DualMT5] consumer "
                f"alive={self._consumer_thread.is_alive()}",
                flush=True,
            )

        print(
            "[DualMT5] STOP 3 - consumer tratado",
            flush=True,
        )

        # ========================================================
        # 3. FECHA AS TRÊS FILAS
        # ========================================================

        for queue_name in (
            "_queue",
            "_win_command_queue",
            "_cfd_command_queue",
        ):
            current_queue = getattr(self, queue_name)

            if current_queue is None:
                continue

            try:
                print(
                    f"[DualMT5] fechando {queue_name}",
                    flush=True,
                )

                current_queue.cancel_join_thread()
                current_queue.close()

            except Exception as exc:
                print(
                    f"[DualMT5] erro fechando "
                    f"{queue_name}: {exc}",
                    flush=True,
                )

            finally:
                setattr(self, queue_name, None)

        print(
            "[DualMT5] STOP 4 - filas tratadas",
            flush=True,
        )

        # ========================================================
        # 4. LIMPA REFERÊNCIAS
        # ========================================================

        # Mantém referências de recursos que ainda estejam ativos,
        # permitindo uma nova tentativa de encerramento.

        if (
            self._win_process is not None
            and self._win_process.pid is not None
            and self._win_process.is_alive()
        ):
            pass
        else:
            self._win_process = None

        if (
            self._cfd_process is not None
            and self._cfd_process.pid is not None
            and self._cfd_process.is_alive()
        ):
            pass
        else:
            self._cfd_process = None

        if (
            self._consumer_thread is not None
            and self._consumer_thread.is_alive()
        ):
            pass
        else:
            self._consumer_thread = None

        print(
            "[DualMT5] STOP 5 - concluído",
            flush=True,
        )

        if shutdown_errors:
            raise RuntimeError(
                "Falha no shutdown do DualMT5FeedService: "
                + "; ".join(shutdown_errors)
            )