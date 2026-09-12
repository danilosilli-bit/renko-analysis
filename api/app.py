from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from ingestion.mt5_realtime_client import (
    MT5RealtimeClient,
)

from services.intraday_market_pipeline import (
    IntradayMarketPipeline,
)

from services.market_service import (
    MarketService,
)

from services.renko_service import (
    RenkoService,
)

from storage.intraday_repository import (
    IntradayRepository,
)

from storage.intraday_storage import (
    reset_intraday_storage,
)

from storage.renko_repository import (
    RenkoRepository,
)

from storage.sqlite_manager import (
    SQLiteManager,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"

BRICK_SIZES = (10, 30, 45)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_ROOT / "web"


# ============================================================
# SERVIÇOS
# ============================================================

mt5_client = MT5RealtimeClient()


market_service = MarketService(
    mt5_client=mt5_client,
    symbol=INTRADAY_SYMBOL,
    poll_interval=0.02,
)


renko_service = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=BRICK_SIZES,
)


intraday_repository = None
intraday_pipeline = None

renko_initialized = False


# ============================================================
# HELPERS
# ============================================================

def serialize_state(state):
    """
    Converte RenkoState para dict serializável pela API.
    """

    if state is None:
        return None

    return {
        "symbol": state.symbol,
        "brick_size": state.brick_size,
        "open_time": state.open_time,
        "open": state.open,
        "last": state.last,
        "high": state.high,
        "low": state.low,
        "direction": state.direction,
        "volume": state.volume,
        "buy_qty": state.buy_qty,
        "sell_qty": state.sell_qty,
        "buy_financial": state.buy_financial,
        "sell_financial": state.sell_financial,
        "trades_count": state.trades_count,
    }


def get_intraday_bricks(
    brick_size: int,
) -> list[dict]:
    """
    Retorna somente os bricks gerados nesta sessão intraday.

    Não usa RenkoService.get_bricks() por enquanto,
    pois esse método ainda pertence ao fluxo antigo
    que utilizava seed artificial.
    """

    repository = renko_service.repositories.get(
        brick_size
    )

    if repository is None:
        return []

    return repository.bricks


def get_latest_intraday_brick(
    brick_size: int,
):
    """
    Retorna o último brick fechado da sessão intraday.
    """

    bricks = get_intraday_bricks(
        brick_size
    )

    if not bricks:
        return None

    return bricks[-1]


# ============================================================
# STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global intraday_repository
    global intraday_pipeline
    global renko_initialized

    # --------------------------------------------------------
    # 1. Limpa armazenamento intraday da sessão anterior
    # --------------------------------------------------------

    print("Resetando armazenamento intraday...")

    reset_intraday_storage()

    print("Armazenamento intraday resetado.")


    # --------------------------------------------------------
    # 2. Abre histórico oficial
    # --------------------------------------------------------

    print(
        f"Carregando estado histórico de "
        f"{HISTORICAL_SYMBOL}..."
    )

    historical_db = SQLiteManager(
        str(HISTORICAL_RENKO_DB)
    )

    historical_repository = RenkoRepository(
        historical_db
    )


    # --------------------------------------------------------
    # 3. Prepara bancos intraday
    # --------------------------------------------------------

    intraday_repository = IntradayRepository()

    intraday_repository.prepare_symbol(
        INTRADAY_SYMBOL
    )


    # --------------------------------------------------------
    # 4. Inicializa os Renko a partir do histórico real
    # --------------------------------------------------------

    renko_service.initialize_from_history(
        historical_repository=
            historical_repository,

        intraday_repository=
            intraday_repository.renko_repository,

        historical_symbol=
            HISTORICAL_SYMBOL,

        intraday_symbol=
            INTRADAY_SYMBOL,
    )

    renko_initialized = True

    print(
        "Renko inicializado pelo histórico: "
        + ", ".join(
            f"{size}R"
            for size in BRICK_SIZES
        )
    )


    # --------------------------------------------------------
    # 5. Cria pipeline intraday
    # --------------------------------------------------------

    intraday_pipeline = IntradayMarketPipeline(
        tick_repository=
            intraday_repository.tick_repository,

        renko_service=
            renko_service,

        symbol=
            INTRADAY_SYMBOL,
    )


    # --------------------------------------------------------
    # 6. Conecta ao MT5
    # --------------------------------------------------------

    print("Conectando ao MT5...")

    mt5_client.connect()

    print("MT5 conectado.")


    # --------------------------------------------------------
    # 7. MarketService -> IntradayMarketPipeline
    # --------------------------------------------------------

    market_service.subscribe(
        intraday_pipeline.process_realtime_tick
    )

    market_service.start()

    print(
        f"MarketService iniciado para "
        f"{INTRADAY_SYMBOL}."
    )


    # --------------------------------------------------------
    # API ativa
    # --------------------------------------------------------

    yield


    # --------------------------------------------------------
    # SHUTDOWN
    # --------------------------------------------------------

    print("Encerrando MarketService...")

    market_service.stop()


    if intraday_pipeline is not None:

        market_service.unsubscribe(
            intraday_pipeline.process_realtime_tick
        )


    print("Desconectando do MT5...")

    mt5_client.disconnect()

    print("MT5 desconectado.")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Renko Analysis API",
    version="0.3.0",
    lifespan=lifespan,
)


app.mount(
    "/static",
    StaticFiles(
        directory=WEB_DIR
    ),
    name="static",
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return FileResponse(
        WEB_DIR / "index.html"
    )


# ============================================================
# STATUS
# ============================================================

@app.get("/api/status")
def status():

    try:

        terminal = mt5_client.get_terminal_info()

        return {
            "mt5_connected":
                mt5_client.connected,

            "terminal_connected":
                terminal.get(
                    "connected"
                ),

            "trade_allowed":
                terminal.get(
                    "trade_allowed"
                ),

            "tradeapi_disabled":
                terminal.get(
                    "tradeapi_disabled"
                ),

            "company":
                terminal.get(
                    "company"
                ),

            "terminal":
                terminal.get(
                    "name"
                ),

            "build":
                terminal.get(
                    "build"
                ),

            "historical_symbol":
                HISTORICAL_SYMBOL,

            "intraday_symbol":
                INTRADAY_SYMBOL,

            "market_service_running":
                market_service.running,

            "received_ticks":
                market_service.received_ticks,

            "renko_initialized":
                renko_initialized,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# ÚLTIMO TICK
# ============================================================

@app.get("/api/tick")
def tick():

    latest_tick = (
        market_service.get_latest_tick()
    )

    if latest_tick is None:

        return {
            "symbol":
                INTRADAY_SYMBOL,

            "status":
                "WAITING_FOR_TICK",
        }

    return {
        "symbol":
            latest_tick.symbol,

        "time_msc":
            latest_tick.timestamp_ms,

        "price":
            latest_tick.price,

        "bid":
            latest_tick.bid,

        "ask":
            latest_tick.ask,

        "last":
            latest_tick.last,

        "spread":
            latest_tick.spread,

        "price_source":
            latest_tick.source_price,
    }


# ============================================================
# ESPECIFICAÇÃO DO ATIVO INTRADAY
# ============================================================

@app.get("/api/symbol")
def symbol():

    try:

        return mt5_client.get_symbol_spec(
            INTRADAY_SYMBOL
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# TODOS OS RENKOS
# ============================================================

@app.get("/api/renko")
def renko():

    if not renko_initialized:

        return {
            "historical_symbol":
                HISTORICAL_SYMBOL,

            "intraday_symbol":
                INTRADAY_SYMBOL,

            "initialized":
                False,

            "brick_sizes":
                BRICK_SIZES,
        }


    result = {
        "historical_symbol":
            HISTORICAL_SYMBOL,

        "intraday_symbol":
            INTRADAY_SYMBOL,

        "initialized":
            True,

        "renko": {},
    }


    for brick_size in BRICK_SIZES:

        bricks = get_intraday_bricks(
            brick_size
        )

        result["renko"][
            str(brick_size)
        ] = {
            "brick_size":
                brick_size,

            "brick_count":
                len(bricks),

            "latest_brick":
                get_latest_intraday_brick(
                    brick_size
                ),

            "state":
                serialize_state(
                    renko_service.get_state(
                        brick_size
                    )
                ),
        }


    return result


# ============================================================
# RENKO POR TAMANHO
# ============================================================

@app.get("/api/renko/{brick_size}")
def renko_by_size(
    brick_size: int,
):

    if brick_size not in BRICK_SIZES:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Renko {brick_size}R "
                f"não configurado."
            ),
        )


    if not renko_initialized:

        return {
            "historical_symbol":
                HISTORICAL_SYMBOL,

            "intraday_symbol":
                INTRADAY_SYMBOL,

            "brick_size":
                brick_size,

            "initialized":
                False,
        }


    bricks = get_intraday_bricks(
        brick_size
    )

    recent_bricks = bricks[-100:]


    return {
        "historical_symbol":
            HISTORICAL_SYMBOL,

        "intraday_symbol":
            INTRADAY_SYMBOL,

        "brick_size":
            brick_size,

        "initialized":
            True,

        "brick_count":
            len(bricks),

        "latest_brick":
            get_latest_intraday_brick(
                brick_size
            ),

        "recent_bricks":
            recent_bricks,

        "state":
            serialize_state(
                renko_service.get_state(
                    brick_size
                )
            ),
    }