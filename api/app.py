from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from ingestion.mt5_intraday_history_client import (
    MT5IntradayHistoryClient,
)

from ingestion.mt5_realtime_client import (
    MT5RealtimeClient,
)

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

HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"

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

win_intraday_pipeline = None
cfd_intraday_pipeline = None

win_source_handoff_service = None
cfd_source_handoff_service = None

dual_feed_service = None

renko_initialized = False

bootstrap_result = None

cfd_symbol_spec = None


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def serialize_state(state):

    if state is None:
        return None

    return {
        "symbol":
            state.symbol,

        "brick_size":
            state.brick_size,

        "open_time":
            state.open_time,

        "open":
            state.open,

        "last":
            state.last,

        "high":
            state.high,

        "low":
            state.low,

        "direction":
            state.direction,

        "volume":
            state.volume,

        "buy_qty":
            state.buy_qty,

        "sell_qty":
            state.sell_qty,

        "buy_financial":
            state.buy_financial,

        "sell_financial":
            state.sell_financial,

        "trades_count":
            state.trades_count,
    }


def serialize_tick(tick):

    if tick is None:
        return None

    return {
        "symbol":
            tick.symbol,

        "time_msc":
            tick.timestamp_ms,

        "price":
            tick.price,

        "bid":
            tick.bid,

        "ask":
            tick.ask,

        "last":
            tick.last,

        "spread":
            tick.spread,

        "price_source":
            tick.source_price,
    }


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


# ============================================================
# STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global intraday_repository
    global historical_repository

    global win_intraday_pipeline
    global cfd_intraday_pipeline

    global win_source_handoff_service
    global cfd_source_handoff_service

    global dual_feed_service

    global renko_initialized
    global bootstrap_result

    global cfd_symbol_spec


    # ========================================================
    # 1. RESET INTRADAY
    # ========================================================

    print("")
    print(
        "========================================"
    )

    print(
        "INICIANDO RENKO ANALYSIS"
    )

    print(
        "========================================"
    )

    print("")
    print(
        "Resetando armazenamento intraday..."
    )


    reset_intraday_storage()


    print(
        "Armazenamento intraday resetado."
    )


    # ========================================================
    # 2. HISTÓRICO OFICIAL
    # ========================================================

    print("")
    print(
        "Carregando Renko histórico..."
    )


    historical_db = SQLiteManager(
        str(
            HISTORICAL_RENKO_DB
        )
    )


    historical_repository = (
        RenkoRepository(
            historical_db
        )
    )


    # ========================================================
    # 3. INTRADAY DATABASE
    # ========================================================

    intraday_repository = (
        IntradayRepository()
    )


    intraday_repository.prepare_symbol(
        HISTORICAL_SYMBOL
    )


    intraday_repository.prepare_symbol(
        INTRADAY_SYMBOL
    )


    print("")
    print(
        "Trilhas intraday preparadas:"
    )

    print(
        f"WIN : {HISTORICAL_SYMBOL}"
    )

    print(
        f"CFD : {INTRADAY_SYMBOL}"
    )


    # ========================================================
    # 4. BOOTSTRAP RENKO PELO HISTÓRICO D-1
    #
    # Nenhum brick de hoje é persistido durante o replay.
    # ========================================================

    bootstrap_renko_service.initialize_from_history(
        historical_repository=
            historical_repository,

        intraday_repository=
            intraday_repository
            .renko_repository,

        historical_symbol=
            HISTORICAL_SYMBOL,

        intraday_symbol=
            HISTORICAL_SYMBOL,

        defer_persistence=
            True,
    )


    print("")
    print(
        "Estado Renko histórico carregado."
    )


    # ========================================================
    # 5. BUSCA TODOS OS TICKS DE HOJE NA XP
    # ========================================================

    print("")
    print(
        "Conectando à XP para bootstrap..."
    )


    xp_history_client = (
        MT5IntradayHistoryClient(
            terminal_path=
                XP_MT5_PATH
        )
    )


    xp_history_client.connect()


    try:

        today_ticks = (
            xp_history_client
            .get_today_ticks(
                HISTORICAL_SYMBOL
            )
        )

    finally:

        xp_history_client.disconnect()


    print(
        f"Ticks recebidos da XP: "
        f"{len(today_ticks)}"
    )


    # ========================================================
    # 6. PROCESSA OS TICKS UMA ÚNICA VEZ
    #
    # Não salvamos cada tick no SQLite.
    #
    # Esta foi a otimização já validada:
    #
    # todos os ticks
    #      ↓
    # Renko em memória
    #      ↓
    # persistência somente dos bricks
    # ========================================================

    print("")
    print(
        "Processando bootstrap Renko..."
    )


    processed_ticks = 0
    last_timestamp_ms = None


    for raw_tick in today_ticks:

        intraday_tick = (
            mt5_history_to_intraday_tick(
                raw_tick,

                symbol=
                    HISTORICAL_SYMBOL,

                source_type=
                    "FUTURES",

                price_source=
                    "last",
            )
        )


        bootstrap_renko_service.process_intraday_tick(
            intraday_tick
        )


        processed_ticks += 1

        last_timestamp_ms = (
            intraday_tick.timestamp_ms
        )


    bootstrap_result = {
        "processed_ticks":
            processed_ticks,

        "last_timestamp_ms":
            last_timestamp_ms,
    }


    print("")
    print(
        "Bootstrap processado."
    )

    print(
        f"processed_ticks   : "
        f"{processed_ticks}"
    )

    print(
        f"last_timestamp_ms : "
        f"{last_timestamp_ms}"
    )


    # ========================================================
    # 7. MOSTRA ESTADO FINAL DO BOOTSTRAP
    # ========================================================

    print("")
    print(
        "ESTADO DEPOIS DO BOOTSTRAP"
    )


    for brick_size in BRICK_SIZES:

        state = (
            bootstrap_renko_service
            .get_state(
                brick_size
            )
        )


        if state is None:

            print(
                f"{brick_size}R | "
                f"state=None"
            )

            continue


        repository = (
            bootstrap_renko_service
            .repositories[
                brick_size
            ]
        )


        print(
            f"{brick_size}R | "
            f"open={state.open} | "
            f"last={state.last} | "
            f"high={state.high} | "
            f"low={state.low} | "
            f"bricks={len(repository.bricks)}"
        )


    # ========================================================
    # 8. SNAPSHOT
    #
    # IMPORTANTE:
    #
    # Snapshot é tirado ANTES da bifurcação.
    # ========================================================

    runtime_snapshot = (
        bootstrap_renko_service
        .get_runtime_snapshot()
    )


    print("")
    print(
        "Snapshot do bootstrap criado."
    )


    # ========================================================
    # 9. PERSISTE OS MESMOS BRICKS NAS DUAS TRILHAS
    #
    # NÃO recalcula Renko.
    #
    # O mesmo conjunto de bricks vai para:
    #
    # renko_winv26
    # renko_bra50oct26
    # ========================================================

    print("")
    print(
        "Persistindo Renko nas duas trilhas..."
    )


    for brick_size in BRICK_SIZES:

        repository = (
            bootstrap_renko_service
            .repositories[
                brick_size
            ]
        )


        brick_count = len(
            repository.bricks
        )


        repository.persist_bricks(
            [
                HISTORICAL_SYMBOL,
                INTRADAY_SYMBOL,
            ]
        )


        print(
            f"{brick_size}R | "
            f"{brick_count} bricks "
            f"-> WIN + CFD"
        )


    # ========================================================
    # 10. BIFURCAÇÃO DOS RUNTIMES
    # ========================================================

    print("")
    print(
        "Criando runtime WIN..."
    )


    win_renko_service.initialize_from_snapshot(
        snapshot=
            runtime_snapshot,

        intraday_repository=
            intraday_repository
            .renko_repository,

        intraday_symbol=
            HISTORICAL_SYMBOL,
    )


    print(
        "Criando runtime CFD..."
    )


    cfd_renko_service.initialize_from_snapshot(
        snapshot=
            runtime_snapshot,

        intraday_repository=
            intraday_repository
            .renko_repository,

        intraday_symbol=
            INTRADAY_SYMBOL,
    )


    renko_initialized = True


    print(
        "Runtimes WIN e CFD criados."
    )


    # ========================================================
    # 11. HANDOFF
    #
    # NÃO existe catch-up.
    #
    # O espaço entre:
    #
    # last_timestamp_ms do bootstrap
    #
    # e
    #
    # primeiro tick realtime
    #
    # permanece sem processamento.
    #
    # O primeiro tick realtime recebe:
    #
    # source_transition=True
    #
    # permitindo a marcação visual da transição/gap.
    # ========================================================

    win_source_handoff_service = (
        SourceHandoffService(
            last_bootstrap_timestamp_ms=
                last_timestamp_ms,

            from_source=
                "FUTURES",

            from_symbol=
                HISTORICAL_SYMBOL,

            to_source=
                "FUTURES",

            to_symbol=
                HISTORICAL_SYMBOL,
        )
    )


    cfd_source_handoff_service = (
        SourceHandoffService(
            last_bootstrap_timestamp_ms=
                last_timestamp_ms,

            from_source=
                "FUTURES",

            from_symbol=
                HISTORICAL_SYMBOL,

            to_source=
                "CFD",

            to_symbol=
                INTRADAY_SYMBOL,
        )
    )


    print("")
    print(
        "Handoffs preparados."
    )


    # ========================================================
    # 12. PIPELINES
    # ========================================================

    win_intraday_pipeline = (
        IntradayMarketPipeline(
            tick_repository=
                intraday_repository
                .tick_repository,

            renko_service=
                win_renko_service,

            symbol=
                HISTORICAL_SYMBOL,

            source_type=
                "FUTURES",
        )
    )


    cfd_intraday_pipeline = (
        IntradayMarketPipeline(
            tick_repository=
                intraday_repository
                .tick_repository,

            renko_service=
                cfd_renko_service,

            symbol=
                INTRADAY_SYMBOL,

            source_type=
                "CFD",
        )
    )


    print(
        "Pipelines WIN e CFD preparados."
    )


    # ========================================================
    # 13. CACHE DA ESPECIFICAÇÃO CFD
    #
    # O processo principal conecta rapidamente à
    # ActivTrades antes de iniciar os workers.
    #
    # Isso preserva /api/symbol sem manter uma terceira
    # conexão MT5 ativa.
    # ========================================================

    print("")
    print(
        "Carregando especificação do CFD..."
    )


    spec_client = MT5RealtimeClient(
        path=
            ACTIVTRADES_MT5_PATH
    )


    try:

        spec_client.connect()

        cfd_symbol_spec = (
            spec_client
            .get_symbol_spec(
                INTRADAY_SYMBOL
            )
        )

    except Exception as exc:

        print(
            "Não foi possível carregar "
            "a especificação CFD: "
            f"{exc}"
        )

        cfd_symbol_spec = None

    finally:

        try:
            spec_client.disconnect()
        except Exception:
            pass


    # ========================================================
    # 14. DUAL MT5 FEED
    #
    # Processo 1:
    # XP / WINV26 / LAST
    #
    # Processo 2:
    # ActivTrades / Bra50Oct26 / BID
    #
    # Ambos enviam RealtimeTick para uma Queue.
    #
    # O processo principal roteia:
    #
    # WIN -> handle_win_realtime_tick
    # CFD -> handle_cfd_realtime_tick
    # ========================================================

    dual_feed_service = (
        DualMT5FeedService(
            win_terminal_path=
                XP_MT5_PATH,

            win_symbol=
                HISTORICAL_SYMBOL,

            cfd_terminal_path=
                ACTIVTRADES_MT5_PATH,

            cfd_symbol=
                INTRADAY_SYMBOL,

            poll_interval=
                0.02,
        )
    )


    dual_feed_service.set_win_callback(
        handle_win_realtime_tick
    )


    dual_feed_service.set_cfd_callback(
        handle_cfd_realtime_tick
    )


    print("")
    print(
        "Iniciando workers MT5..."
    )


    dual_feed_service.start()


    print(
        "Dual MT5 Feed iniciado."
    )

    print("")
    print(
        "XP          -> WINV26      -> LAST"
    )

    print(
        "ActivTrades -> Bra50Oct26  -> BID"
    )

    print("")
    print(
        "Aguardando ticks realtime..."
    )


    # ========================================================
    # API ATIVA
    # ========================================================

    yield


    # ========================================================
    # SHUTDOWN
    # ========================================================

    print("")
    print(
        "Encerrando Dual MT5 Feed..."
    )


    if dual_feed_service is not None:

        dual_feed_service.stop()


    print(
        "Dual MT5 Feed encerrado."
    )


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Renko Analysis API",
    version="0.5.0",
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