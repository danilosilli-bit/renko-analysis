import time

from ingestion.mt5_realtime_client import (
    MT5RealtimeClient,
)

from services.market_service import (
    MarketService,
)


from config.storage_config import (
    HISTORICAL_RENKO_DB,
)

from ingestion.mt5_intraday_history_client import (
    MT5IntradayHistoryClient,
)

from services.intraday_tick_adapter import (
    mt5_history_to_intraday_tick,
)

from storage.sqlite_manager import (
    SQLiteManager,
)

from storage.renko_repository import (
    RenkoRepository,
)

from storage.intraday_repository import (
    IntradayRepository,
)

from storage.intraday_storage import (
    reset_intraday_storage,
)

from services.renko_service import (
    RenkoService,
)


XP_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
)

HISTORICAL_SYMBOL = "WINV26"
INTRADAY_SYMBOL = "Bra50Oct26"

BRICK_SIZES = (
    10,
    30,
    45,
)


def state_values(state):

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


# ============================================================
# RESET INTRADAY
# ============================================================

print()

print("RESET INTRADAY")
print("=" * 40)

reset_intraday_storage()


# ============================================================
# HISTÓRICO RENKO D-1
# ============================================================

historical_renko_db = SQLiteManager(
    str(HISTORICAL_RENKO_DB)
)

historical_renko_repository = (
    RenkoRepository(
        historical_renko_db
    )
)


# ============================================================
# INTRADAY
# ============================================================

intraday_repository = (
    IntradayRepository()
)

# Trilha Renko WIN
intraday_repository.prepare_symbol(
    HISTORICAL_SYMBOL
)

# Trilha Renko CFD
intraday_repository.prepare_symbol(
    INTRADAY_SYMBOL
)


# ============================================================
# RENKO BOOTSTRAP
# ============================================================

renko_service = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=BRICK_SIZES,
)

renko_service.initialize_from_history(
    historical_repository=
        historical_renko_repository,

    intraday_repository=
        intraday_repository.renko_repository,

    historical_symbol=
        HISTORICAL_SYMBOL,

    intraday_symbol=
        HISTORICAL_SYMBOL,

    defer_persistence=True,
)


# ============================================================
# ESTADO ANTES DO REPLAY
# ============================================================

print()

print("ESTADO ANTES DO REPLAY")
print("=" * 40)

for brick_size in BRICK_SIZES:

    state = renko_service.engines[
        brick_size
    ].state

    print(
        f"{brick_size}R | "
        f"open={state.open} | "
        f"last={state.last}"
    )


# ============================================================
# XP MT5
# ============================================================

print()

print("CONECTANDO À XP")
print("=" * 40)

xp_client = MT5IntradayHistoryClient(
    terminal_path=XP_MT5_PATH
)

xp_client.connect()

raw_ticks = []
processed_ticks = 0
last_timestamp_ms = None


try:

    raw_ticks = xp_client.get_today_ticks(
        HISTORICAL_SYMBOL
    )

    print(
        "ticks recebidos da XP :",
        len(raw_ticks)
    )


    # ========================================================
    # REPLAY DO DIA
    # ========================================================

    print()

    print("REPLAY DO DIA")
    print("=" * 40)


    for raw_tick in raw_ticks:

        tick = (
            mt5_history_to_intraday_tick(
                tick=raw_tick,
                symbol=HISTORICAL_SYMBOL,
                source_type="FUTURES",
                price_source="last",
            )
        )


        # ----------------------------------------------------
        # NÃO persiste o tick.
        #
        # O tick é processado somente uma vez pelo RenkoEngine.
        # ----------------------------------------------------

        renko_service.process_intraday_tick(
            tick
        )

        processed_ticks += 1

        last_timestamp_ms = (
            tick.timestamp_ms
        )


finally:

    xp_client.disconnect()


# ============================================================
# RESULTADO DO PROCESSAMENTO
# ============================================================

print()

print("RESULTADO DO PROCESSAMENTO")
print("=" * 40)

print(
    "received_ticks     :",
    len(raw_ticks),
)

print(
    "processed_ticks    :",
    processed_ticks,
)

print(
    "last_timestamp_ms  :",
    last_timestamp_ms,
)


# ============================================================
# ESTADO DEPOIS DO REPLAY
# ============================================================

print()

print("ESTADO DEPOIS DO REPLAY")
print("=" * 40)

for brick_size in BRICK_SIZES:

    state = renko_service.engines[
        brick_size
    ].state

    repository = (
        renko_service.repositories[
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


# ============================================================
# SNAPSHOT FINAL DO BOOTSTRAP
# ============================================================

runtime_snapshot = (
    renko_service
    .get_runtime_snapshot()
)


# ============================================================
# PERSISTÊNCIA DOS RENKOS
# ============================================================

print()

print("PERSISTINDO RENKOS")
print("=" * 40)

for brick_size in BRICK_SIZES:

    repository = (
        renko_service.repositories[
            brick_size
        ]
    )

    brick_count = len(
        repository.bricks
    )

    print(
        f"{brick_size}R | "
        f"persistindo {brick_count} bricks "
        f"em WIN e CFD"
    )

    repository.persist_bricks(
        target_symbols=(
            HISTORICAL_SYMBOL,
            INTRADAY_SYMBOL,
        )
    )


# ============================================================
# VALIDAÇÃO DOS BANCOS
# ============================================================

print()

print("VALIDAÇÃO DAS TRILHAS")
print("=" * 40)

for symbol in (
    HISTORICAL_SYMBOL,
    INTRADAY_SYMBOL,
):

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
            SELECT
                brick_size,
                COUNT(*)
            FROM {table_name}
            GROUP BY brick_size
            ORDER BY brick_size
            """
        )
    )

    print()
    print(symbol)

    for row in rows:

        print(
            f"{int(row[0])}R | "
            f"{row[1]} bricks"
        )


# ============================================================
# CRIAÇÃO DOS DOIS RUNTIMES
# ============================================================

print()

print("CRIANDO RUNTIMES WIN E CFD")
print("=" * 40)


win_runtime = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=BRICK_SIZES,
)


cfd_runtime = RenkoService(
    symbol=HISTORICAL_SYMBOL,
    brick_sizes=BRICK_SIZES,
)


win_runtime.initialize_from_snapshot(
    snapshot=runtime_snapshot,

    intraday_repository=(
        intraday_repository
        .renko_repository
    ),

    intraday_symbol=HISTORICAL_SYMBOL,
)


cfd_runtime.initialize_from_snapshot(
    snapshot=runtime_snapshot,

    intraday_repository=(
        intraday_repository
        .renko_repository
    ),

    intraday_symbol=INTRADAY_SYMBOL,
)


# ============================================================
# VALIDAÇÃO DA BIFURCAÇÃO
# ============================================================

print()

print("VALIDAÇÃO DO ESTADO DOS RUNTIMES")
print("=" * 40)


all_runtime_states_ok = True


for brick_size in BRICK_SIZES:

    bootstrap_engine = (
        renko_service.engines[
            brick_size
        ]
    )

    win_engine = (
        win_runtime.engines[
            brick_size
        ]
    )

    cfd_engine = (
        cfd_runtime.engines[
            brick_size
        ]
    )


    bootstrap_state = (
        bootstrap_engine.state
    )

    win_state = (
        win_engine.state
    )

    cfd_state = (
        cfd_engine.state
    )


    bootstrap_values = (
        state_values(
            bootstrap_state
        )
    )

    win_values = (
        state_values(
            win_state
        )
    )

    cfd_values = (
        state_values(
            cfd_state
        )
    )


    same_values = (
        bootstrap_values
        == win_values
        == cfd_values
    )


    independent_states = (
        bootstrap_state
        is not win_state
        and
        bootstrap_state
        is not cfd_state
        and
        win_state
        is not cfd_state
    )


    independent_last_bricks = (
        bootstrap_engine.last_closed_brick
        is not
        win_engine.last_closed_brick

        and

        bootstrap_engine.last_closed_brick
        is not
        cfd_engine.last_closed_brick

        and

        win_engine.last_closed_brick
        is not
        cfd_engine.last_closed_brick
    )


    same_last_brick_values = (
        bootstrap_engine.last_closed_brick
        ==
        win_engine.last_closed_brick
        ==
        cfd_engine.last_closed_brick
    )


    print()

    print(
        f"{brick_size}R"
    )

    print("-" * 40)

    print(
        "mesmos valores state       :",
        same_values,
    )

    print(
        "states independentes        :",
        independent_states,
    )

    print(
        "mesmo último brick          :",
        same_last_brick_values,
    )

    print(
        "últimos bricks independentes:",
        independent_last_bricks,
    )

    print(
        "bootstrap last              :",
        bootstrap_state.last,
    )

    print(
        "WIN runtime last            :",
        win_state.last,
    )

    print(
        "CFD runtime last            :",
        cfd_state.last,
    )


    if not (
        same_values
        and independent_states
        and same_last_brick_values
        and independent_last_bricks
    ):
        all_runtime_states_ok = False


# ============================================================
# RESULTADO FINAL
# ============================================================

print()

print("=" * 40)


if not all_runtime_states_ok:

    raise AssertionError(
        "Falha ao bifurcar o estado "
        "final do bootstrap."
    )


print(
    "RUNTIMES WIN E CFD "
    "CRIADOS COM SUCESSO"
)

print()

print(
    "bootstrap único -> "
    "WIN runtime + CFD runtime"
)

print()

print(
    "Os dois runtimes possuem "
    "o mesmo estado inicial, "
    "mas objetos independentes."
)

print()

print("BOOTSTRAP CONCLUÍDO")
print("=" * 40)

# ============================================================
# XP REALTIME APÓS O BOOTSTRAP
# ============================================================

print()
print()
print("XP REALTIME APÓS O BOOTSTRAP")
print("=" * 40)


# ------------------------------------------------------------
# Guarda os estados imediatamente após a bifurcação.
#
# A partir daqui:
#
# WIN runtime recebe XP realtime
# CFD runtime NÃO recebe nenhum tick
#
# Portanto:
#
# WIN deve mudar
# CFD deve permanecer exatamente igual
# ------------------------------------------------------------

win_before_realtime = {}
cfd_before_realtime = {}


for brick_size in BRICK_SIZES:

    win_before_realtime[
        brick_size
    ] = state_values(
        win_runtime.engines[
            brick_size
        ].state
    )

    cfd_before_realtime[
        brick_size
    ] = state_values(
        cfd_runtime.engines[
            brick_size
        ].state
    )


# ============================================================
# XP REALTIME CLIENT
# ============================================================

xp_realtime_client = (
    MT5RealtimeClient(
        path=XP_MT5_PATH,
    )
)


xp_realtime_client.connect()


try:

    account = (
        xp_realtime_client
        .get_account_info()
    )


    print(
        "company :",
        account.get("company"),
    )

    print(
        "server  :",
        account.get("server"),
    )


    # ========================================================
    # MARKET SERVICE WIN
    # ========================================================

    win_market_service = (
        MarketService(
            mt5_client=
                xp_realtime_client,

            symbol=
                HISTORICAL_SYMBOL,

            poll_interval=0.02,
        )
    )


    # --------------------------------------------------------
    # SOMENTE WIN recebe os ticks realtime.
    #
    # CFD runtime permanece totalmente parado.
    # --------------------------------------------------------

    win_market_service.subscribe(
        win_runtime.process_tick
    )


    TEST_SECONDS = 10


    print()

    print(
        f"Monitorando WIN realtime "
        f"por {TEST_SECONDS}s..."
    )


    win_market_service.start()


    try:

        time.sleep(
            TEST_SECONDS
        )

    finally:

        win_market_service.stop()


    # ========================================================
    # RESULTADO DO FEED
    # ========================================================

    print()

    print("RESULTADO DO FEED WIN")
    print("=" * 40)


    print(
        "ticks recebidos :",
        win_market_service
        .received_ticks,
    )


    latest_tick = (
        win_market_service
        .get_latest_tick()
    )


    if latest_tick is not None:

        print(
            "último timestamp :",
            latest_tick.timestamp_ms,
        )

        print(
            "último preço     :",
            latest_tick.price,
        )

        print(
            "fonte do preço   :",
            latest_tick.source_price,
        )


    # ========================================================
    # VALIDAÇÃO DOS DOIS RUNTIMES
    # ========================================================

    print()

    print(
        "VALIDAÇÃO APÓS XP REALTIME"
    )

    print("=" * 40)


    all_win_changed = True
    all_cfd_unchanged = True


    for brick_size in BRICK_SIZES:

        win_after_realtime = (
            state_values(
                win_runtime.engines[
                    brick_size
                ].state
            )
        )

        cfd_after_realtime = (
            state_values(
                cfd_runtime.engines[
                    brick_size
                ].state
            )
        )


        win_changed = (
            win_after_realtime
            !=
            win_before_realtime[
                brick_size
            ]
        )


        cfd_unchanged = (
            cfd_after_realtime
            ==
            cfd_before_realtime[
                brick_size
            ]
        )


        if not win_changed:

            all_win_changed = False


        if not cfd_unchanged:

            all_cfd_unchanged = False


        print()

        print(
            f"{brick_size}R"
        )

        print("-" * 40)


        print(
            "WIN mudou          :",
            win_changed,
        )

        print(
            "CFD permaneceu igual:",
            cfd_unchanged,
        )


        print(
            "WIN before last     :",
            win_before_realtime[
                brick_size
            ]["last"],
        )

        print(
            "WIN after last      :",
            win_after_realtime[
                "last"
            ],
        )

        print(
            "WIN high            :",
            win_after_realtime[
                "high"
            ],
        )

        print(
            "WIN low             :",
            win_after_realtime[
                "low"
            ],
        )


        print(
            "CFD before last     :",
            cfd_before_realtime[
                brick_size
            ]["last"],
        )

        print(
            "CFD after last      :",
            cfd_after_realtime[
                "last"
            ],
        )


    # ========================================================
    # VALIDAÇÃO FINAL
    # ========================================================

    print()

    print("=" * 40)


    if (
        win_market_service
        .received_ticks
        <= 0
    ):

        raise AssertionError(
            "Nenhum tick realtime "
            "foi recebido da XP."
        )


    if not all_win_changed:

        raise AssertionError(
            "O WIN recebeu ticks realtime, "
            "mas algum estado Renko "
            "não mudou."
        )


    if not all_cfd_unchanged:

        raise AssertionError(
            "O CFD runtime mudou mesmo "
            "sem receber ticks."
        )


    print(
        "RESULTADO: "
        "BOOTSTRAP -> "
        "WIN REALTIME OK"
    )

    print(
        "CFD RUNTIME "
        "PERMANECEU INDEPENDENTE"
    )


finally:

    xp_realtime_client.disconnect()

# ============================================================
# CFD REALTIME APÓS O BOOTSTRAP
# ============================================================

print()
print()
print("CFD REALTIME APÓS O BOOTSTRAP")
print("=" * 40)


ACTIVTRADES_MT5_PATH = (
    r"C:\Program Files\MetaTrader 5 - ActivTrades\terminal64.exe"
)


# ------------------------------------------------------------
# Neste ponto o teste XP realtime já terminou e o cliente XP
# já foi desconectado pelo finally anterior.
#
# Agora guardamos o estado atual dos dois runtimes.
#
# A partir daqui:
#
# CFD runtime recebe ActivTrades realtime
# WIN runtime NÃO recebe nenhum tick
# ------------------------------------------------------------

win_before_cfd_realtime = {}
cfd_before_cfd_realtime = {}


for brick_size in BRICK_SIZES:

    win_before_cfd_realtime[
        brick_size
    ] = state_values(
        win_runtime.engines[
            brick_size
        ].state
    )

    cfd_before_cfd_realtime[
        brick_size
    ] = state_values(
        cfd_runtime.engines[
            brick_size
        ].state
    )


# ============================================================
# ACTIVTRADES REALTIME CLIENT
# ============================================================

cfd_realtime_client = (
    MT5RealtimeClient(
        path=ACTIVTRADES_MT5_PATH,
    )
)


cfd_realtime_client.connect()


try:

    account = (
        cfd_realtime_client
        .get_account_info()
    )


    print(
        "company :",
        account.get("company"),
    )

    print(
        "server  :",
        account.get("server"),
    )


    raw_cfd_tick = (
        cfd_realtime_client
        .get_tick(
            INTRADAY_SYMBOL
        )
    )


    print()

    print("TICK CFD INICIAL")
    print("-" * 40)

    print(
        "bid  :",
        raw_cfd_tick["bid"],
    )

    print(
        "ask  :",
        raw_cfd_tick["ask"],
    )

    print(
        "last :",
        raw_cfd_tick["last"],
    )


    # ========================================================
    # MARKET SERVICE CFD
    # ========================================================

    cfd_market_service = (
        MarketService(
            mt5_client=
                cfd_realtime_client,

            symbol=
                INTRADAY_SYMBOL,

            poll_interval=0.02,
        )
    )


    # --------------------------------------------------------
    # SOMENTE CFD recebe os ticks da ActivTrades.
    #
    # WIN runtime permanece parado.
    # --------------------------------------------------------

    cfd_market_service.subscribe(
        cfd_runtime.process_tick
    )


    CFD_TEST_SECONDS = 10


    print()

    print(
        f"Monitorando CFD realtime "
        f"por {CFD_TEST_SECONDS}s..."
    )


    cfd_market_service.start()


    try:

        time.sleep(
            CFD_TEST_SECONDS
        )

    finally:

        cfd_market_service.stop()


    # ========================================================
    # RESULTADO DO FEED CFD
    # ========================================================

    print()

    print("RESULTADO DO FEED CFD")
    print("=" * 40)


    print(
        "ticks recebidos :",
        cfd_market_service
        .received_ticks,
    )


    latest_cfd_tick = (
        cfd_market_service
        .get_latest_tick()
    )


    if latest_cfd_tick is not None:

        print(
            "último timestamp :",
            latest_cfd_tick.timestamp_ms,
        )

        print(
            "último BID       :",
            latest_cfd_tick.bid,
        )

        print(
            "último LAST      :",
            latest_cfd_tick.last,
        )

        print(
            "último preço     :",
            latest_cfd_tick.price,
        )

        print(
            "fonte do preço   :",
            latest_cfd_tick.source_price,
        )


    # ========================================================
    # VALIDAÇÃO DOS DOIS RUNTIMES
    # ========================================================

    print()

    print(
        "VALIDAÇÃO APÓS CFD REALTIME"
    )

    print("=" * 40)


    all_cfd_changed = True
    all_win_unchanged = True


    for brick_size in BRICK_SIZES:

        win_after_cfd_realtime = (
            state_values(
                win_runtime.engines[
                    brick_size
                ].state
            )
        )

        cfd_after_cfd_realtime = (
            state_values(
                cfd_runtime.engines[
                    brick_size
                ].state
            )
        )


        cfd_changed = (
            cfd_after_cfd_realtime
            !=
            cfd_before_cfd_realtime[
                brick_size
            ]
        )


        win_unchanged = (
            win_after_cfd_realtime
            ==
            win_before_cfd_realtime[
                brick_size
            ]
        )


        if not cfd_changed:

            all_cfd_changed = False


        if not win_unchanged:

            all_win_unchanged = False


        print()

        print(
            f"{brick_size}R"
        )

        print("-" * 40)


        print(
            "CFD mudou          :",
            cfd_changed,
        )

        print(
            "WIN permaneceu igual:",
            win_unchanged,
        )


        print(
            "CFD before last     :",
            cfd_before_cfd_realtime[
                brick_size
            ]["last"],
        )

        print(
            "CFD after last      :",
            cfd_after_cfd_realtime[
                "last"
            ],
        )

        print(
            "CFD high            :",
            cfd_after_cfd_realtime[
                "high"
            ],
        )

        print(
            "CFD low             :",
            cfd_after_cfd_realtime[
                "low"
            ],
        )


        print(
            "WIN before last     :",
            win_before_cfd_realtime[
                brick_size
            ]["last"],
        )

        print(
            "WIN after last      :",
            win_after_cfd_realtime[
                "last"
            ],
        )


    # ========================================================
    # VALIDAÇÃO FINAL
    # ========================================================

    print()

    print("=" * 40)


    if (
        cfd_market_service
        .received_ticks
        <= 0
    ):

        raise AssertionError(
            "Nenhum tick realtime "
            "foi recebido da ActivTrades."
        )


    if latest_cfd_tick is None:

        raise AssertionError(
            "Nenhum RealtimeTick CFD "
            "foi recebido."
        )


    if (
        latest_cfd_tick.source_price
        !=
        "bid"
    ):

        raise AssertionError(
            "CFD realtime não está "
            "usando BID."
        )


    if (
        latest_cfd_tick.price
        !=
        latest_cfd_tick.bid
    ):

        raise AssertionError(
            "Preço analítico do CFD "
            "é diferente do BID."
        )


    if not all_cfd_changed:

        raise AssertionError(
            "O CFD recebeu ticks realtime, "
            "mas algum estado Renko "
            "não mudou."
        )


    if not all_win_unchanged:

        raise AssertionError(
            "O WIN runtime mudou durante "
            "o processamento do CFD."
        )


    print(
        "RESULTADO: "
        "BOOTSTRAP -> "
        "CFD REALTIME OK"
    )

    print(
        "WIN RUNTIME "
        "PERMANECEU INDEPENDENTE"
    )


finally:

    cfd_realtime_client.disconnect()