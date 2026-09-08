import threading
import time
from collections.abc import Callable

from ingestion.mt5_realtime_client import MT5RealtimeClient
from market.realtime_tick import RealtimeTick, from_mt5_tick


TickCallback = Callable[[RealtimeTick], None]


class MarketService:
    """
    Serviço responsável por:

    1. Ler ticks do MT5.
    2. Ignorar leituras repetidas do mesmo tick.
    3. Converter o tick bruto para RealtimeTick.
    4. Disponibilizar o último tick recebido.
    5. Distribuir novos ticks para subscribers.

    Não executa ordens.
    Não conhece Renko.
    """

    def __init__(
        self,
        mt5_client: MT5RealtimeClient,
        symbol: str,
        poll_interval: float = 0.02,
    ):
        self.mt5_client = mt5_client
        self.symbol = symbol
        self.poll_interval = poll_interval

        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._subscribers: list[TickCallback] = []

        self._latest_tick: RealtimeTick | None = None
        self._last_timestamp_ms: int | None = None

        self._received_ticks = 0

        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        return self._running

    @property
    def received_ticks(self) -> int:
        return self._received_ticks

    def get_latest_tick(self) -> RealtimeTick | None:
        with self._lock:
            return self._latest_tick

    def subscribe(self, callback: TickCallback) -> None:
        """
        Registra uma função que será chamada sempre que chegar
        um NOVO tick.
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: TickCallback) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def start(self) -> None:
        if self._running:
            return

        self.mt5_client.ensure_connected()
        self.mt5_client.ensure_symbol(self.symbol)

        self._stop_event.clear()
        self._running = True

        self._thread = threading.Thread(
            target=self._run,
            name=f"MarketService-{self.symbol}",
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            return

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=2.0)

        self._running = False
        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                raw_tick = self.mt5_client.get_tick(self.symbol)

                timestamp_ms = int(raw_tick["time_msc"])

                # get_tick() pode devolver o mesmo tick várias vezes.
                if timestamp_ms == self._last_timestamp_ms:
                    time.sleep(self.poll_interval)
                    continue

                tick = from_mt5_tick(
                    symbol=self.symbol,
                    tick=raw_tick,
                )

                self._last_timestamp_ms = tick.timestamp_ms

                with self._lock:
                    self._latest_tick = tick
                    self._received_ticks += 1

                self._notify(tick)

            except Exception as exc:
                print(
                    f"[MarketService] erro ao processar "
                    f"{self.symbol}: {exc}"
                )

                time.sleep(0.5)

            time.sleep(self.poll_interval)

    def _notify(self, tick: RealtimeTick) -> None:
        for callback in self._subscribers.copy():
            try:
                callback(tick)
            except Exception as exc:
                print(
                    f"[MarketService] erro no subscriber "
                    f"{callback}: {exc}"
                )