from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ingestion.mt5_realtime_client import MT5RealtimeClient



SYMBOL = "Bra50"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_ROOT / "web"

mt5_client = MT5RealtimeClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Conectando ao MT5...")
    mt5_client.connect()
    print("MT5 conectado.")

    yield

    print("Desconectando do MT5...")
    mt5_client.disconnect()


app = FastAPI(
    title="Renko Analysis API",
    version="0.1.0",
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
            "terminal_connected": terminal.get("connected"),
            "trade_allowed": terminal.get("trade_allowed"),
            "tradeapi_disabled": terminal.get("tradeapi_disabled"),
            "company": terminal.get("company"),
            "terminal": terminal.get("name"),
            "build": terminal.get("build"),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.get("/api/tick")
def tick():
    try:
        data = mt5_client.get_tick(SYMBOL)

        return {
            "symbol": SYMBOL,
            "time": data.get("time"),
            "time_msc": data.get("time_msc"),
            "bid": data.get("bid"),
            "ask": data.get("ask"),
            "last": data.get("last"),
            "spread": data.get("spread_price"),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.get("/api/symbol")
def symbol():
    try:
        return mt5_client.get_symbol_spec(SYMBOL)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )