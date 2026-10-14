from api.serializers import (
    serialize_state,
    serialize_tick,
)

from contextlib import asynccontextmanager
from pathlib import Path


from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routers.trading import (
    configure_trading_router,
    router as trading_router,
)

from trading.broker_router import (
    BrokerRouter,
)

from trading.trading_service import (
    TradingService,
)

from trading.renko_30r_signal import (
    Renko30RSignal,
)

from trading.order_guard import (
    OrderGuard,
)

from trading.operation_manager import (
    OperationManager,
)

from storage.trading_operation_repository import (
    TradingOperationRepository,
)


from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from ingestion.mt5_intraday_history_client import (
    MT5IntradayHistoryClient,
)

from ingestion.mt5_realtime_client import (
    MT5RealtimeClient,
)

from services.application_runtime import ApplicationRuntime

from services.dual_mt5_feed_service import (
    DualMT5FeedService,
)

from services.intraday_market_pipeline import (
    IntradayMarketPipeline,
)

from services.intraday_tick_adapter import (
    mt5_history_to_intraday_tick,
)

from services.renko_service import (
    RenkoService,
)

from services.source_handoff_service import (
    SourceHandoffService,
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

HISTORICAL_SYMBOL = "WINZ26"
INTRADAY_SYMBOL = "Bra50Dec26"

BRICK_SIZES = (
    10,
    30,
    45,
)


# ============================================================
# TERMINAIS MT5
# ============================================================

XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal"
    r"\terminal64.exe"
)

ACTIVTRADES_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 - ActivTrades"
    r"\terminal64.exe"
)


# ============================================================
# WEB
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

WEB_DIR = (
    PROJECT_ROOT / "web"
)


# ============================================================
# RENKO SERVICES
# ============================================================

# ------------------------------------------------------------
# BOOTSTRAP
#
# Processa os ticks XP de hoje UMA única vez.
# ------------------------------------------------------------

bootstrap_renko_service = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=BRICK_SIZES,
)


# ------------------------------------------------------------
# WIN RUNTIME
#
# Depois do bootstrap:
#
# XP / WINV26 / LAST
# ------------------------------------------------------------

win_renko_service = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=BRICK_SIZES,
)


# ------------------------------------------------------------
# CFD RUNTIME
#
# Depois do bootstrap:
#
# ActivTrades / Bra50Oct26 / BID
#
# Mantemos symbol=WINV26 no RenkoService.
# Isso preserva a configuração Renko já validada.
# ------------------------------------------------------------

cfd_renko_service = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=BRICK_SIZES,
)


# ============================================================
# ESTADO GLOBAL
# ============================================================

intraday_repository = None

historical_repository = None

application_runtime = None

win_intraday_pipeline = None
cfd_intraday_pipeline = None

win_source_handoff_service = None
cfd_source_handoff_service = None

dual_feed_service = None

broker_router = None
trading_service = None

renko_initialized = False

bootstrap_result = None

cfd_symbol_spec = None


# ============================================================
# SERIALIZAÇÃO
# ============================================================



# ============================================================
# INTRADAY RENKO HELPERS
# ============================================================

def get_intraday_bricks(
    brick_size: int,
    symbol: str,
) -> list[dict]:

    if intraday_repository is None:
        return []

    table_name = (
        intraday_repository
        .renko_repository
        .get_table_name(
            symbol
        )
    )

    rows = (
        intraday_repository
        .renko_db
        .execute(
            f"""
            SELECT *
            FROM {table_name}
            WHERE brick_size = ?
            ORDER BY id
            """,
            (
                brick_size,
            ),
        )
    )

    return [
        dict(row)
        for row in rows
    ]


def get_latest_intraday_brick(
    brick_size: int,
    symbol: str,
):

    bricks = get_intraday_bricks(
        brick_size=brick_size,
        symbol=symbol,
    )

    if not bricks:
        return None

    return bricks[-1]


# ============================================================
# HANDOFF WIN
# ============================================================

def handle_win_realtime_tick(tick):

    if (
        win_source_handoff_service
        is None
    ):
        return

    if (
        win_intraday_pipeline
        is None
    ):
        return


    handoff_result = (
        win_source_handoff_service
        .accept_realtime_tick(
            tick.timestamp_ms
        )
    )


    if not handoff_result[
        "accepted"
    ]:
        return


    source_transition = (
        handoff_result[
            "source_transition"
        ]
    )


    if source_transition:

        print("")
        print(
            "WIN entrou em realtime."
        )

        print(
            "Gap anterior mantido "
            "intencionalmente."
        )

        print(
            "Primeiro tick WIN marcado "
            "como source_transition."
        )


    win_intraday_pipeline.process_realtime_tick(
        tick,
        source_transition=
            source_transition,
    )


# ============================================================
# HANDOFF CFD
# ============================================================

def handle_cfd_realtime_tick(tick):

    if (
        cfd_source_handoff_service
        is None
    ):
        return

    if (
        cfd_intraday_pipeline
        is None
    ):
        return


    handoff_result = (
        cfd_source_handoff_service
        .accept_realtime_tick(
            tick.timestamp_ms
        )
    )


    if not handoff_result[
        "accepted"
    ]:
        return


    source_transition = (
        handoff_result[
            "source_transition"
        ]
    )


    if source_transition:

        print("")
        print(
            "CFD entrou em realtime."
        )

        print(
            "Gap anterior mantido "
            "intencionalmente."
        )

        print(
            "Primeiro tick CFD marcado "
            "como source_transition."
        )


    cfd_intraday_pipeline.process_realtime_tick(
        tick,
        source_transition=
            source_transition,
    )

def create_application_runtime() -> ApplicationRuntime:
    return ApplicationRuntime(
        historical_symbol=HISTORICAL_SYMBOL,
        intraday_symbol=INTRADAY_SYMBOL,
        bootstrap_renko_service=RenkoService(
            symbol=HISTORICAL_SYMBOL,
            brick_sizes=BRICK_SIZES,
        ),
        xp_terminal_path=XP_MT5_PATH,
        brick_sizes=list(BRICK_SIZES),
        win_renko_service=RenkoService(
            symbol=HISTORICAL_SYMBOL,
            brick_sizes=BRICK_SIZES,
        ),
        cfd_renko_service=RenkoService(
            symbol=HISTORICAL_SYMBOL,
            brick_sizes=BRICK_SIZES,
        ),
        activtrades_terminal_path=ACTIVTRADES_MT5_PATH,
    )

# ============================================================
# STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global application_runtime

    global intraday_repository
    global historical_repository

    global win_intraday_pipeline
    global cfd_intraday_pipeline

    global win_source_handoff_service
    global cfd_source_handoff_service

    global dual_feed_service
    global trading_service

    global renko_initialized
    global bootstrap_result
    global cfd_symbol_spec

    application_runtime = create_application_runtime()

    try:
        # ====================================================
        # 1. INICIALIZA INFRAESTRUTURA DE MERCADO
        # ====================================================

        application_runtime.start()

        # ====================================================
        # 2. EXPÕE REFERÊNCIAS PARA OS ENDPOINTS
        # ====================================================

        intraday_repository = (
            application_runtime.intraday_repository
        )

        historical_repository = (
            application_runtime.historical_repository
        )

        win_intraday_pipeline = (
            application_runtime.win_intraday_pipeline
        )

        cfd_intraday_pipeline = (
            application_runtime.cfd_intraday_pipeline
        )

        win_source_handoff_service = (
            application_runtime.win_source_handoff_service
        )

        cfd_source_handoff_service = (
            application_runtime.cfd_source_handoff_service
        )

        dual_feed_service = (
            application_runtime.dual_feed_service
        )

        bootstrap_result = (
            application_runtime.bootstrap_result
        )

        cfd_symbol_spec = (
            application_runtime.cfd_symbol_spec
        )

        # Os endpoints utilizam os serviços Renko globais.
        # Portanto, apontamos para os serviços do runtime.

        global win_renko_service
        global cfd_renko_service

        win_renko_service = (
            application_runtime.win_renko_service
        )

        cfd_renko_service = (
            application_runtime.cfd_renko_service
        )

        renko_initialized = True

        # ====================================================
        # 3. CONFIGURA TRADING
        # ====================================================

        broker_router = BrokerRouter()

        broker_router.register(
            broker_id="xp",
            feed_service=dual_feed_service,
            feed="WIN",
            symbol=HISTORICAL_SYMBOL,
        )

        broker_router.register(
            broker_id="activtrades",
            feed_service=dual_feed_service,
            feed="CFD",
            symbol=dual_feed_service.cfd_symbol,
        )

        order_guard = OrderGuard(
            signal_provider=get_trading_signal
        )

        trading_operation_repository = (
            TradingOperationRepository(
                db_path="data/trading/trading.db"
            )
        )

        operation_manager = OperationManager(
            repository=trading_operation_repository
        )

        trading_service = TradingService(
            broker_router=broker_router,
            broker_id="xp",
            order_guard=order_guard,
            operation_manager=operation_manager,
        )

        configure_trading_router(
            trading_service
        )

        print("Trading Service configurado.")

        # ====================================================
        # 4. API ATIVA
        # ====================================================

        yield

    finally:
        # ====================================================
        # 5. SHUTDOWN
        # ====================================================

        try:
            application_runtime.stop()
        finally:
            renko_initialized = False

# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Renko Analysis API",
    version="0.5.0",
    lifespan=lifespan,
)


app.include_router(
    trading_router
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

    win_tick = None
    cfd_tick = None


    if dual_feed_service is not None:

        win_tick = (
            dual_feed_service
            .get_latest_win_tick()
        )

        cfd_tick = (
            dual_feed_service
            .get_latest_cfd_tick()
        )


    return {
        "dual_feed_running":
            (
                dual_feed_service.running
                if dual_feed_service
                is not None
                else False
            ),

        "renko_initialized":
            renko_initialized,

        "bootstrap":
            bootstrap_result,

        "win": {
            "symbol":
                HISTORICAL_SYMBOL,

            "received_ticks":
                (
                    dual_feed_service
                    .win_received_ticks
                    if dual_feed_service
                    is not None
                    else 0
                ),

            "latest_tick":
                serialize_tick(
                    win_tick
                ),

            "runtime_initialized":
                bool(
                    win_renko_service
                    .engines
                ),
        },

        "cfd": {
            "symbol":
                INTRADAY_SYMBOL,

            "received_ticks":
                (
                    dual_feed_service
                    .cfd_received_ticks
                    if dual_feed_service
                    is not None
                    else 0
                ),

            "latest_tick":
                serialize_tick(
                    cfd_tick
                ),

            "runtime_initialized":
                bool(
                    cfd_renko_service
                    .engines
                ),
        },
    }



# ============================================================
# TICKS
# ============================================================

@app.get("/api/tick")
def tick():

    if dual_feed_service is None:

        return {
            "status":
                "WAITING_FOR_FEEDS",

            "win":
                None,

            "cfd":
                None,
        }


    win_tick = (
        dual_feed_service
        .get_latest_win_tick()
    )


    cfd_tick = (
        dual_feed_service
        .get_latest_cfd_tick()
    )


    return {
        "status":
            (
                "REALTIME"
                if (
                    win_tick is not None
                    and
                    cfd_tick is not None
                )
                else
                "WAITING_FOR_TICKS"
            ),

        "win":
            serialize_tick(
                win_tick
            ),

        "cfd":
            serialize_tick(
                cfd_tick
            ),
    }


# ============================================================
# ESPECIFICAÇÃO CFD
#
# Preserva o endpoint utilizado pela interface.
# ============================================================

@app.get("/api/symbol")
def symbol():

    if cfd_symbol_spec is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "Especificação CFD "
                "não disponível."
            ),
        )


    return cfd_symbol_spec


# ============================================================
# RENKO
#
# Por enquanto este endpoint continua representando
# a trilha CFD para preservar o gráfico atual.
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

        "renko":
            {},
    }


    for brick_size in BRICK_SIZES:

        bricks = (
            get_intraday_bricks(
                brick_size=
                    brick_size,

                symbol=
                    INTRADAY_SYMBOL,
            )
        )


        result[
            "renko"
        ][
            str(brick_size)
        ] = {

            "brick_size":
                brick_size,

            "brick_count":
                len(
                    bricks
                ),

            "latest_brick":
                (
                    get_latest_intraday_brick(
                        brick_size=
                            brick_size,

                        symbol=
                            INTRADAY_SYMBOL,
                    )
                ),

            "state":
                serialize_state(
                    cfd_renko_service
                    .get_state(
                        brick_size
                    )
                ),
        }


    return result


# ============================================================
# RENKO CFD POR TAMANHO
#
# Continua alimentando o gráfico atual.
# ============================================================

@app.get(
    "/api/renko/{brick_size}"
)
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


    intraday_bricks = (
        get_intraday_bricks(
            brick_size=
                brick_size,

            symbol=
                INTRADAY_SYMBOL,
        )
    )


    historical_bricks = (
        historical_repository
        .get_recent_closed_bricks(
            HISTORICAL_SYMBOL,
            brick_size,
            100,
        )
    )


    combined_bricks = (
        historical_bricks
        +
        intraday_bricks
    )


    recent_bricks = (
        combined_bricks[
            -100:
        ]
    )


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
            len(
                recent_bricks
            ),

        "historical_brick_count":
            len(
                historical_bricks
            ),

        "intraday_brick_count":
            len(
                intraday_bricks
            ),

        "latest_brick":
            (
                get_latest_intraday_brick(
                    brick_size=
                        brick_size,

                    symbol=
                        INTRADAY_SYMBOL,
                )
            ),

        "recent_bricks":
            recent_bricks,

        "state":
            serialize_state(
                cfd_renko_service
                .get_state(
                    brick_size
                )
            ),
    }

# ============================================================
# RENKO CFD - REALTIME
#
# Endpoint leve para atualização rápida do gráfico.
# Não consulta histórico nem reconstrói a série Renko.
# ============================================================

@app.get(
    "/api/renko/{brick_size}/realtime"
)
def renko_realtime_by_size(
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
            "brick_size":
                brick_size,

            "initialized":
                False,
        }

    return {
        "brick_size":
            brick_size,

        "initialized":
            True,

        "runtime_bricks":
            cfd_renko_service
            .get_runtime_bricks(
                brick_size
            ),

        "runtime_brick_count":
            len(
                cfd_renko_service
                .get_runtime_bricks(
                    brick_size
                )
            ),

        "state":
            serialize_state(
                cfd_renko_service
                .get_state(
                    brick_size
                )
            ),
    }


# ============================================================
# RENKO WIN
#
# Endpoint adicional.
#
# Não interfere no gráfico CFD atual.
# ============================================================

@app.get(
    "/api/renko-win/{brick_size}"
)
def renko_win_by_size(
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
            "symbol":
                HISTORICAL_SYMBOL,

            "brick_size":
                brick_size,

            "initialized":
                False,
        }


    intraday_bricks = (
        get_intraday_bricks(
            brick_size=
                brick_size,

            symbol=
                HISTORICAL_SYMBOL,
        )
    )


    historical_bricks = (
        historical_repository
        .get_recent_closed_bricks(
            HISTORICAL_SYMBOL,
            brick_size,
            100,
        )
    )


    combined_bricks = (
        historical_bricks
        +
        intraday_bricks
    )


    recent_bricks = (
        combined_bricks[
            -100:
        ]
    )


    return {
        "symbol":
            HISTORICAL_SYMBOL,

        "brick_size":
            brick_size,

        "initialized":
            True,

        "intraday_brick_count":
            len(
                intraday_bricks
            ),

        "recent_bricks":
            recent_bricks,

        "state":
            serialize_state(
                win_renko_service
                .get_state(
                    brick_size
                )
            ),
    }

# ============================================================
# RENKO WIN - REALTIME
#
# Endpoint leve para atualização rápida do gráfico.
# Não consulta histórico nem reconstrói a série Renko.
# ============================================================

@app.get(
    "/api/renko-win/{brick_size}/realtime"
)
def renko_win_realtime_by_size(
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
            "brick_size":
                brick_size,

            "initialized":
                False,
        }

    return {
        "brick_size":
            brick_size,

        "initialized":
            True,

        "runtime_bricks":
            win_renko_service
            .get_runtime_bricks(
                brick_size
            ),

        "runtime_brick_count":
            len(
                win_renko_service
                .get_runtime_bricks(
                    brick_size
                )
            ),

        "state":
            serialize_state(
                win_renko_service
                .get_state(
                    brick_size
                )
            ),
    }



# ============================================================
# SINAL OPERACIONAL RENKO 30R
#
# Somente leitura.
# Não envia ordens e não altera posições.
# ============================================================

def get_trading_signal(
    market: str,
) -> dict:

    market = market.upper().strip()


    if market not in (
        "WIN",
        "CFD",
    ):
        return {
            "ready": False,
            "direction": None,
            "can_buy": False,
            "can_sell": False,
            "max_stop_price": None,
            "reason":
                "Mercado inválido.",
        }


    if not renko_initialized:

        return {
            "ready": False,
            "direction": None,
            "can_buy": False,
            "can_sell": False,
            "max_stop_price": None,
            "reason":
                "Renko não inicializado.",
        }


    if market == "WIN":

        intraday_symbol = (
            HISTORICAL_SYMBOL
        )

    else:

        intraday_symbol = (
            INTRADAY_SYMBOL
        )


    intraday_bricks = (
        get_intraday_bricks(
            brick_size=30,
            symbol=intraday_symbol,
        )
    )


    historical_bricks = (
        historical_repository
        .get_recent_closed_bricks(
            HISTORICAL_SYMBOL,
            30,
            100,
        )
    )


    combined_bricks = (
        historical_bricks
        +
        intraday_bricks
    )


    signal = Renko30RSignal()


    return signal.evaluate_bricks(
        combined_bricks
    )

@app.get(
    "/api/trading-signal/cfd"
)
def cfd_trading_signal():

    result = get_trading_signal(
        "CFD"
    )

    return {
        "market": "CFD",
        "initialized":
            renko_initialized,
        **result,
    }


@app.get(
    "/api/trading-signal/win"
)
def win_trading_signal():

    result = get_trading_signal(
        "WIN"
    )

    return {
        "market": "WIN",
        "initialized":
            renko_initialized,
        **result,
    }