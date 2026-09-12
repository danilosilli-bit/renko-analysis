from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ingestion.mt5_realtime_client import MT5RealtimeClient
from services.market_service import MarketService
from services.renko_service import RenkoService


SYMBOL = "Bra50"
BRICK_SIZES = (10, 30, 45)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_ROOT / "web"


mt5_client = MT5RealtimeClient()

market_service = MarketService(
    mt5_client=mt5_client,
    symbol=SYMBOL,
    poll_interval=0.02,
)

renko_service = RenkoService(
    symbol=SYMBOL,
    brick_sizes=BRICK_SIZES,
)

renko_initialized = False


def handle_market_tick(tick):
    """
    Recebe o RealtimeTick produzido pelo MarketService.

    O primeiro tick válido inicializa os motores Renko.
    Depois disso, todos os ticks seguem normalmente
    para o RenkoService.
    """
    global renko_initialized

    if not renko_initialized:

        if tick.price <= 0:
            return

        renko_service.initialize(
            initial_price=tick.price
        )

        renko_initialized = True

        print(
            f"Renko inicializado em {tick.price} "
            f"({', '.join(f'{size}R' for size in BRICK_SIZES)})"
        )

    renko_service.process_tick(tick)


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


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Conectando ao MT5...")

    mt5_client.connect()

    print("MT5 conectado.")

    market_service.subscribe(
        handle_market_tick
    )

    market_service.start()

    print(
        f"MarketService iniciado para {SYMBOL}."
    )

    yield

    print("Encerrando MarketService...")

    market_service.stop()

    if renko_initialized:
        renko_service.flush()

    market_service.unsubscribe(
        handle_market_tick
    )

    print("Desconectando do MT5...")

    mt5_client.disconnect()

    print("MT5 desconectado.")


app = FastAPI(
    title="Renko Analysis API",
    version="0.2.0",
    lifespan=lifespan,
)


app.mount(
    "/static",
    StaticFiles(directory=WEB_DIR),
    name="static",
)


@app.get("/")
def home():
    return FileResponse(
        WEB_DIR / "index.html"
    )


@app.get("/api/status")
def status():

    try:
        terminal = mt5_client.get_terminal_info()

        return {
            "mt5_connected": mt5_client.connected,
            "terminal_connected": terminal.get(
                "connected"
            ),
            "trade_allowed": terminal.get(
                "trade_allowed"
            ),
            "tradeapi_disabled": terminal.get(
                "tradeapi_disabled"
            ),
            "company": terminal.get(
                "company"
            ),
            "terminal": terminal.get(
                "name"
            ),
            "build": terminal.get(
                "build"
            ),

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


@app.get("/api/tick")
def tick():

    latest_tick = market_service.get_latest_tick()

    if latest_tick is None:
        return {
            "symbol": SYMBOL,
            "status": "WAITING_FOR_TICK",
        }

    return {
        "symbol": latest_tick.symbol,
        "time_msc": latest_tick.timestamp_ms,

        "price": latest_tick.price,

        "bid": latest_tick.bid,
        "ask": latest_tick.ask,
        "last": latest_tick.last,

        "spread": latest_tick.spread,

        "price_source":
            latest_tick.source_price,
    }


@app.get("/api/symbol")
def symbol():

    try:
        return mt5_client.get_symbol_spec(
            SYMBOL
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.get("/api/renko")
def renko():

    if not renko_initialized:
        return {
            "symbol": SYMBOL,
            "initialized": False,
            "brick_sizes": BRICK_SIZES,
        }

    result = {
        "symbol": SYMBOL,
        "initialized": True,
        "renko": {},
    }

    for brick_size in BRICK_SIZES:

        bricks = renko_service.get_bricks(
            brick_size
        )

        result["renko"][str(brick_size)] = {
            "brick_size": brick_size,

            "brick_count":
                len(bricks),

            "latest_brick":
                renko_service.get_latest_brick(
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


@app.get("/api/renko/{brick_size}")
def renko_by_size(brick_size: int):

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
            "symbol": SYMBOL,
            "brick_size": brick_size,
            "initialized": False,
        }

    bricks = renko_service.get_bricks(
        brick_size
    )

    recent_bricks = bricks[-100:]

    return {
        "symbol": SYMBOL,
        "brick_size": brick_size,
        "initialized": True,

        "brick_count":
            len(bricks),

        "latest_brick":
            renko_service.get_latest_brick(
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