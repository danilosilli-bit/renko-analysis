import multiprocessing as mp
import queue
import threading

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

        self._queue = (
            self._context.Queue()
        )

        self.win_received_ticks = 0
        self.cfd_received_ticks = 0

        self.latest_win_tick = None
        self.latest_cfd_tick = None

        self._running = True


        # ----------------------------------------------------
        # XP / WIN
        # ----------------------------------------------------

        self._win_process = (
            self._context.Process(
                target=run_mt5_feed_worker,
                kwargs={
                    "feed_name":
                        "WIN",

                    "terminal_path":
                        self.win_terminal_path,

                    "symbol":
                        self.win_symbol,

                    "output_queue":
                        self._queue,

                    "poll_interval":
                        self.poll_interval,
                },
                name="mt5-win-feed",
            )
        )


        # ----------------------------------------------------
        # ACTIVTRADES / CFD
        # ----------------------------------------------------

        self._cfd_process = (
            self._context.Process(
                target=run_mt5_feed_worker,
                kwargs={
                    "feed_name":
                        "CFD",

                    "terminal_path":
                        self.cfd_terminal_path,

                    "symbol":
                        self.cfd_symbol,

                    "output_queue":
                        self._queue,

                    "poll_interval":
                        self.poll_interval,
                },
                name="mt5-cfd-feed",
            )
        )


        # ----------------------------------------------------
        # CONSUMIDOR DA QUEUE
        #
        # Esta thread existe no processo principal.
        # Portanto os RenkoService continuam no mesmo
        # processo da API.
        # ----------------------------------------------------

        self._consumer_thread = (
            threading.Thread(
                target=self._consume_queue,
                name="dual-mt5-queue-consumer",
                daemon=True,
            )
        )


        self._win_process.start()
        self._cfd_process.start()

        self._consumer_thread.start()


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


    # ========================================================
    # STOP
    # ========================================================

    def stop(self) -> None:

        if not self._running:
            return

        self._running = False


        # ----------------------------------------------------
        # Finaliza os workers.
        # ----------------------------------------------------

        for process in (
            self._win_process,
            self._cfd_process,
        ):

            if process is None:
                continue

            if process.is_alive():

                process.terminate()


            process.join(
                timeout=5
            )


        # ----------------------------------------------------
        # Aguarda a thread consumidora.
        # ----------------------------------------------------

        if (
            self._consumer_thread
            is not None
        ):

            self._consumer_thread.join(
                timeout=2
            )


        # ----------------------------------------------------
        # Fecha a Queue.
        # ----------------------------------------------------

        if self._queue is not None:

            try:

                self._queue.close()

                self._queue.join_thread()

            except Exception:
                pass


        self._win_process = None
        self._cfd_process = None

        self._consumer_thread = None

        self._queue = None