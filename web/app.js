const statusDot =
    document.getElementById(
        "status-dot"
    );

const connectionStatus =
    document.getElementById(
        "connection-status"
    );

const mt5Status =
    document.getElementById(
        "mt5-status"
    );

const marketStatus =
    document.getElementById(
        "market-status"
    );

const lastTick =
    document.getElementById(
        "last-tick"
    );

const bid =
    document.getElementById(
        "bid"
    );

const ask =
    document.getElementById(
        "ask"
    );

const last =
    document.getElementById(
        "last"
    );

const spread =
    document.getElementById(
        "spread"
    );

const symbol =
    document.getElementById(
        "symbol"
    );

const description =
    document.getElementById(
        "description"
    );


const RENKO_SIZES =
    [10, 30, 45];


const renkoChartCache = {
    CFD: {},
    WIN: {}
};

for (const market of ["CFD", "WIN"]) {

    for (const brickSize of RENKO_SIZES) {

        renkoChartCache[market][brickSize] = {
            closedBricks: [],
            state: null,
            latestClosedKey: null
        };
    }
}

function getRenkoBrickKey(brick) {
    if (!brick) {
        return null;
    }

    return [
        brick.close_time,
        brick.open,
        brick.close
    ].join("|");
}

let selectedMarket = "CFD";

const marketCfdButton =
    document.getElementById("market-cfd");

const marketWinButton =
    document.getElementById("market-win");

function setSelectedMarket(
    market
) {
    selectedMarket = market;

    marketCfdButton?.classList.toggle(
        "active",
        market === "CFD"
    );

    marketWinButton?.classList.toggle(
        "active",
        market === "WIN"
    );

    symbol.textContent =
        market === "WIN"
            ? "WINV26"
            : "Bra50Oct26";

    const chartSymbols =
        document.querySelectorAll(
            ".chart-symbol"
        );

    chartSymbols.forEach(
        element => {
            element.textContent =
                market === "WIN"
                    ? "WINV26"
                    : "Bra50Oct26";
        }
    );
}

marketCfdButton?.addEventListener(
    "click",
    async () => {

        setSelectedMarket("CFD");

        await Promise.all([
            updateDashboard(),
            loadRenkoCharts()
        ]);
    }
);

marketWinButton?.addEventListener(
    "click",
    async () => {

        setSelectedMarket("WIN");

        await Promise.all([
            updateDashboard(),
            loadRenkoCharts()
        ]);
    }
);


function formatPrice(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "-";
    }


    return Number(value)
        .toLocaleString(
            "pt-BR",
            {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            }
        );
}


function setConnectionState(
    connected
) {

    if (connected) {

        statusDot.classList.remove(
            "offline"
        );

        statusDot.classList.add(
            "online"
        );

        connectionStatus.textContent =
            "ONLINE";

    } else {

        statusDot.classList.remove(
            "online"
        );

        statusDot.classList.add(
            "offline"
        );

        connectionStatus.textContent =
            "OFFLINE";
    }
}

function updateMarketStatus(
    timeMsc
) {

    if (!timeMsc) {

        marketStatus.textContent =
            "SEM DADOS";

        marketStatus.className =
            "market-status market-offline";

        lastTick.textContent =
            "-";

        return;
    }


    const now =
        Date.now();

    const age =
        now - timeMsc;


    if (age <= 10000) {

        marketStatus.textContent =
            "LIVE";

        marketStatus.className =
            "market-status market-live";

    } else {

        marketStatus.textContent =
            "STALE / MERCADO FECHADO";

        marketStatus.className =
            "market-status market-stale";
    }


    const date =
        new Date(timeMsc);


    lastTick.textContent =
        date.toLocaleString(
            "pt-BR"
        );
}


function getRenkoPanelElements(
    brickSize
) {

    return {

        direction:
            document.getElementById(
                `renko-${brickSize}-direction`
            ),

        open:
            document.getElementById(
                `renko-${brickSize}-open`
            ),

        last:
            document.getElementById(
                `renko-${brickSize}-last`
            ),

        high:
            document.getElementById(
                `renko-${brickSize}-high`
            ),

        low:
            document.getElementById(
                `renko-${brickSize}-low`
            ),

        count:
            document.getElementById(
                `renko-${brickSize}-count`
            ),

        latest:
            document.getElementById(
                `renko-${brickSize}-latest`
            )
    };
}


function updateRenkoPanel(
    brickSize,
    data
) {

    const elements =
        getRenkoPanelElements(
            brickSize
        );


    if (!data) {
        return;
    }


    const state =
        data.state;


    elements.count.textContent =
        data.brick_count ?? 0;


    if (!state) {

        elements.direction.textContent =
            "-";

        elements.open.textContent =
            "-";

        elements.last.textContent =
            "-";

        elements.high.textContent =
            "-";

        elements.low.textContent =
            "-";

    } else {

        elements.direction.textContent =
            state.direction ??
            "BUILDING";

        elements.open.textContent =
            formatPrice(
                state.open
            );

        elements.last.textContent =
            formatPrice(
                state.last
            );

        elements.high.textContent =
            formatPrice(
                state.high
            );

        elements.low.textContent =
            formatPrice(
                state.low
            );
    }


    const latestBrick =
        data.latest_brick;


    if (!latestBrick) {

        elements.latest.textContent =
            "Nenhum brick fechado";

        elements.latest.className =
            "renko-latest";

        return;
    }


    const direction =
        latestBrick.direction ??
        "-";


    elements.latest.textContent =
        `${direction} | ` +
        `${formatPrice(
            latestBrick.open
        )} → ` +
        `${formatPrice(
            latestBrick.close
        )}`;


    elements.latest.className =
        "renko-latest";


    if (
        direction === "UP"
    ) {

        elements.latest.classList.add(
            "renko-up"
        );

    } else if (
        direction === "DOWN"
    ) {

        elements.latest.classList.add(
            "renko-down"
        );
    }
}


/*
    FUNÇÃO GENÉRICA DE GRÁFICO

    Serve para:
    10R
    30R
    45R
*/

function resizeCanvasToContainer(canvas) {

    const container =
        canvas.parentElement;

    if (!container) {
        return;
    }

    const rect =
        container.getBoundingClientRect();

    const width =
        Math.max(
            Math.floor(rect.width),
            1
        );

    const height =
        Math.max(
            Math.floor(rect.height),
            1
        );

    if (
        canvas.width !== width ||
        canvas.height !== height
    ) {

        canvas.width =
            width;

        canvas.height =
            height;
    }
}

function drawRenkoChart(
    brickSize,
    bricks,
    openState = null
) {

    const canvas =
        document.getElementById(
            `renko-${brickSize}-chart`
        );

    const emptyMessage =
        document.getElementById(
            `renko-${brickSize}-chart-empty`
        );

    const countElement =
        document.getElementById(
            `renko-${brickSize}-chart-count`
        );


    if (!canvas) {
        return;
    }

    resizeCanvasToContainer(
        canvas
    );


    const ctx =
        canvas.getContext(
            "2d"
        );


    const width =
        canvas.width;

    const height =
        canvas.height;


    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    /*
        SEM BRICKS
    */

    if (
        !bricks ||
        bricks.length === 0
    ) {

        emptyMessage.style.display =
            "flex";

        countElement.textContent =
            "0 bricks";

        return;
    }


    emptyMessage.style.display =
        "none";


    /*
        Até 50 bricks por gráfico.
    */

    const closedBricks =
        bricks.slice(
            openState ? -49 : -50
        );

        const visibleBricks =
            openState
                ? [
                    ...closedBricks,
                    {
                        open: openState.open,
                        close: openState.last,
                        high: openState.high,
                        low: openState.low,
                        direction:
                            Number(openState.last) >=
                            Number(openState.open)
                                ? "UP"
                                : "DOWN",
                        source_transition: false,
                        is_open: true
                    }
                ]
                : closedBricks;


    countElement.textContent =
        `${closedBricks.length} bricks`;


    /*
        Para calcular a escala vertical,
        usamos HIGH e LOW.

        Isso é importante agora que
        estamos desenhando pavios.
    */

    const prices = [];


    visibleBricks.forEach(
        brick => {

            prices.push(
                Number(brick.high)
            );

            prices.push(
                Number(brick.low)
            );

            prices.push(
                Number(brick.open)
            );

            prices.push(
                Number(brick.close)
            );
        }
    );


    const actualMinPrice =
        Math.min(...prices);

    const actualMaxPrice =
        Math.max(...prices);


    /*
        Mantemos alguma margem,
        mesmo quando existem poucos
        bricks no gráfico.
    */

    const actualRange =
        actualMaxPrice -
        actualMinPrice;


    const minimumRange =
        Math.max(
            brickSize * 10,
            100
        );


    const displayRange =
        Math.max(
            actualRange,
            minimumRange
        );


    const centerPrice =
        (
            actualMaxPrice +
            actualMinPrice
        ) / 2;


    const minPrice =
        centerPrice -
        displayRange / 2;


    const maxPrice =
        centerPrice +
        displayRange / 2;


    /*
        ÁREA DO GRÁFICO
    */

    const paddingTop = 30;
    const paddingBottom = 50;
    const paddingLeft = 80;
    const paddingRight = 25;


    const chartWidth =
        width -
        paddingLeft -
        paddingRight;


    const chartHeight =
        height -
        paddingTop -
        paddingBottom;


    /*
        LARGURA DOS BRICKS
    */

    const availableWidth =
        chartWidth /
        Math.max(
            visibleBricks.length,
            1
        );


    const brickWidth =
        Math.min(
            28,
            Math.max(
                8,
                availableWidth - 3
            )
        );


    const gap = 3;


    /*
        CONVERSÃO PREÇO → Y
    */

    function priceToY(price) {

        const ratio =
            (
                maxPrice -
                price
            ) /
            (
                maxPrice -
                minPrice
            );


        return (
            paddingTop +
            ratio *
            chartHeight
        );
    }


    /*
        GRID HORIZONTAL
    */

    ctx.strokeStyle =
        "#374151";

    ctx.lineWidth = 1;

    ctx.fillStyle =
        "#9ca3af";

    ctx.font =
        "12px Arial";


    const gridLines = 5;


    for (
        let i = 0;
        i <= gridLines;
        i++
    ) {

        const ratio =
            i / gridLines;


        const y =
            paddingTop +
            ratio *
            chartHeight;


        const price =
            maxPrice -
            ratio *
            (
                maxPrice -
                minPrice
            );


        ctx.beginPath();

        ctx.moveTo(
            paddingLeft,
            y
        );

        ctx.lineTo(
            width -
            paddingRight,
            y
        );

        ctx.stroke();


        ctx.fillText(
            Math.round(price)
                .toLocaleString(
                    "pt-BR"
                ),
            8,
            y + 4
        );
    }


    /*
        Se houver poucos bricks,
        deixamos os dados encostados
        à direita.
    */

    const totalBrickWidth =
        visibleBricks.length *
        (
            brickWidth +
            gap
        );


    const startX =
        Math.max(
            paddingLeft,
            width -
            paddingRight -
            totalBrickWidth
        );


    /*
        DESENHO DOS BRICKS
    */

    visibleBricks.forEach(
        (brick, index) => {

            const open =
                Number(
                    brick.open
                );

            const close =
                Number(
                    brick.close
                );

            const high =
                Number(
                    brick.high
                );

            const low =
                Number(
                    brick.low
                );

            const direction =
                brick.direction;


            const openY =
                priceToY(
                    open
                );

            const closeY =
                priceToY(
                    close
                );

            const highY =
                priceToY(
                    high
                );

            const lowY =
                priceToY(
                    low
                );


            const top =
                Math.min(
                    openY,
                    closeY
                );


            let brickHeight =
                Math.abs(
                    closeY -
                    openY
                );


            brickHeight =
                Math.max(
                    brickHeight,
                    4
                );


            const x =
                startX +
                index *
                (
                    brickWidth +
                    gap
                );


            const centerX =
                x +
                brickWidth / 2;


            /*
                COR

                Bricks gerados durante a
                transição FUTURES -> CFD
                são exibidos em cinza.
            */

            const sourceTransition =
                brick.source_transition === true ||
                brick.source_transition === 1;

            const isOpen =
                brick.is_open === true;

            if (
                isOpen
            ) {

                ctx.fillStyle =
                    direction === "UP"
                        ? "rgba(34, 197, 94, 0.35)"
                        : "rgba(239, 68, 68, 0.35)";

                ctx.strokeStyle =
                    direction === "UP"
                        ? "#4ade80"
                        : "#f87171";

            } else if (
                sourceTransition
            ) {

                ctx.fillStyle =
                    "#6b7280";

                ctx.strokeStyle =
                    "#9ca3af";

            } else if (
                direction === "UP"
            ) {

                ctx.fillStyle =
                    "#22c55e";

                ctx.strokeStyle =
                    "#4ade80";

            } else {

                ctx.fillStyle =
                    "#ef4444";

                ctx.strokeStyle =
                    "#f87171";
            }


            /*
                PAVIO HIGH / LOW
            */

            ctx.beginPath();

            ctx.moveTo(
                centerX,
                highY
            );

            ctx.lineTo(
                centerX,
                lowY
            );

            ctx.stroke();


            /*
                CORPO OPEN / CLOSE
            */

            ctx.fillRect(
                x,
                top,
                brickWidth,
                brickHeight
            );


            ctx.strokeRect(
                x,
                top,
                brickWidth,
                brickHeight
            );
        }
    );

    /*
        EIXO X - HORÁRIOS
    */

    const timeLabelCount = 5;

    ctx.fillStyle = "#9ca3af";
    ctx.font = "11px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    for (
        let labelIndex = 0;
        labelIndex < timeLabelCount;
        labelIndex++
    ) {

        const brickIndex =
            Math.round(
                labelIndex *
                (visibleBricks.length - 1) /
                (timeLabelCount - 1)
            );

        const brick =
            visibleBricks[brickIndex];

        if (
            !brick ||
            !brick.close_time
        ) {
            continue;
        }

        const date =
            new Date(
                brick.close_time
            );

        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            continue;
        }

        const timeText =
            date.toLocaleTimeString(
                "pt-BR",
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false
                }
            );

        const x =
            startX +
            brickIndex *
            (
                brickWidth +
                gap
            ) +
            brickWidth / 2;

        const y =
            paddingTop +
            chartHeight +
            10;

        ctx.fillText(
            timeText,
            x,
            y
        );
    }    
}


async function loadSymbol() {

    try {

        const response =
            await fetch(
                "/api/symbol"
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        symbol.textContent =
            data.name;


        description.textContent =
            data.description;


    } catch (error) {

        console.error(
            "Erro ao carregar símbolo:",
            error
        );
    }
}


async function loadStatus() {
    try {
        const response = await fetch("/api/status");

        if (!response.ok) {
            setConnectionState(false);
            return;
        }

        const data = await response.json();

        const xpStatus = document.getElementById("xp-status");
        const xpStatusDot = document.getElementById("xp-status-dot");

        const activtradesStatus =
            document.getElementById("activtrades-status");

        const activtradesStatusDot =
            document.getElementById("activtrades-status-dot");


        const winConnected =
            data.dual_feed_running === true &&
            data.win?.received_ticks > 0;


        const cfdConnected =
            data.dual_feed_running === true &&
            data.cfd?.received_ticks > 0;


        if (xpStatus) {
            xpStatus.textContent =
                winConnected
                    ? "CONNECTED"
                    : "DISCONNECTED";
        }

        if (xpStatusDot) {
            xpStatusDot.classList.toggle(
                "online",
                winConnected
            );

            xpStatusDot.classList.toggle(
                "offline",
                !winConnected
            );
        }


        if (activtradesStatus) {
            activtradesStatus.textContent =
                cfdConnected
                    ? "CONNECTED"
                    : "DISCONNECTED";
        }

        if (activtradesStatusDot) {
            activtradesStatusDot.classList.toggle(
                "online",
                cfdConnected
            );

            activtradesStatusDot.classList.toggle(
                "offline",
                !cfdConnected
            );
        }


        const connected =
            winConnected &&
            cfdConnected;

        setConnectionState(connected);

    } catch (error) {

        setConnectionState(false);

        console.error(
            "Erro status:",
            error
        );
    }
}


async function loadTick() {
    try {
        const response = await fetch("/api/tick");

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        const tick =
            selectedMarket === "WIN"
                ? data.win
                : data.cfd;

        if (!tick) {
            updateMarketStatus(null);
            return;
        }

        bid.textContent =
            formatPrice(tick.bid);

        ask.textContent =
            formatPrice(tick.ask);

        last.textContent =
            formatPrice(tick.last);

        spread.textContent =
            formatPrice(tick.spread);

        updateMarketStatus(
            tick.time_msc
        );

    } catch (error) {
        console.error(
            "Erro tick:",
            error
        );
    }
}


async function loadRenkoPanels() {

    try {

        const baseEndpoint =
            selectedMarket === "WIN"
                ? "/api/renko-win"
                : "/api/renko";


        const responses =
            await Promise.all(

                RENKO_SIZES.map(
                    brickSize =>
                        fetch(
                            `${baseEndpoint}/${brickSize}`
                        )
                )
            );


        const dataList =
            await Promise.all(

                responses.map(
                    async response => {

                        if (!response.ok) {
                            return null;
                        }

                        return await response.json();
                    }
                )
            );


        RENKO_SIZES.forEach(
            (brickSize, index) => {

                const data =
                    dataList[index];

                if (
                    !data ||
                    data.initialized !== true
                ) {
                    return;
                }


                const recentBricks =
                    data.recent_bricks || [];


                const latestBrick =
                    data.latest_brick ||
                    data.latest_intraday_brick ||
                    (
                        recentBricks.length > 0
                            ? recentBricks[
                                recentBricks.length - 1
                            ]
                            : null
                    );


                updateRenkoPanel(
                    brickSize,
                    {
                        state:
                            data.state,

                        brick_count:
                            data.intraday_brick_count ??
                            data.brick_count ??
                            recentBricks.length,

                        latest_brick:
                            latestBrick
                    }
                );
            }
        );


    } catch (error) {

        console.error(
            "Erro painéis Renko:",
            error
        );
    }
}

async function loadRenkoChart(
    brickSize
) {

    try {

        const baseEndpoint =
            selectedMarket === "WIN"
                ? "/api/renko-win"
                : "/api/renko";


        const response =
            await fetch(
                `${baseEndpoint}/${brickSize}`
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        if (
            data.initialized !== true
        ) {

            drawRenkoChart(
                brickSize,
                []
            );

            return;
        }


        const cache =
            renkoChartCache[
                selectedMarket
            ][
                brickSize
            ];

        cache.closedBricks =
            data.recent_bricks || [];

        cache.state =
            data.state || null;

        const lastClosedBrick =
            cache.closedBricks.length > 0
                ? cache.closedBricks[
                    cache.closedBricks.length - 1
                ]
                : null;

        cache.latestClosedKey =
            lastClosedBrick
                ? `${lastClosedBrick.close_time}|${lastClosedBrick.open}|${lastClosedBrick.close}`
                : null;


        drawRenkoChart(
            brickSize,
            cache.closedBricks,
            cache.state
        );


    } catch (error) {

        console.error(
            `Erro gráfico ${brickSize}R:`,
            error
        );
    }
}

async function loadRenkoRealtime(
    brickSize
) {
    try {

        const baseEndpoint =
            selectedMarket === "WIN"
                ? "/api/renko-win"
                : "/api/renko";

        const response =
            await fetch(
                `${baseEndpoint}/${brickSize}/realtime`,
                {
                    cache: "no-store"
                }
            );

        if (!response.ok) {
            return null;
        }

        const data =
            await response.json();

        if (
            data.initialized !== true
        ) {
            return null;
        }

        return data;

    } catch (error) {

        console.error(
            `Erro realtime ${brickSize}R:`,
            error
        );

        return null;
    }
}


async function loadRenkoCharts() {

    await Promise.all(

        RENKO_SIZES.map(
            brickSize =>
                loadRenkoChart(
                    brickSize
                )
        )
    );
}


/*
    ATUALIZAÇÃO GERAL DO DASHBOARD
*/

async function updateDashboard() {

    await Promise.all([

        loadStatus(),

        loadTick(),

        loadRenkoPanels()

    ]);
}


/*
    ATUALIZAÇÃO DOS GRÁFICOS RENKO
*/

async function updateRenkoRealtime() {
    await Promise.all(
        RENKO_SIZES.map(
            async brickSize => {
                const marketAtRequest =
                    selectedMarket;

                const data =
                    await loadRenkoRealtime(
                        brickSize
                    );

                if (
                    !data ||
                    !data.state
                ) {
                    return;
                }

                // Se o usuário mudou de mercado
                // enquanto a requisição estava em andamento,
                // ignoramos a resposta antiga.
                if (
                    marketAtRequest !==
                    selectedMarket
                ) {
                    return;
                }

                const cache =
                    renkoChartCache[
                        marketAtRequest
                    ][
                        brickSize
                    ];

                if (
                    !cache ||
                    cache.closedBricks.length === 0
                ) {
                    return;
                }

                const runtimeBricks =
                    data.runtime_bricks || [];

                for (
                    const brick
                    of runtimeBricks
                ) {
                    const brickKey =
                        getRenkoBrickKey(
                            brick
                        );

                    const alreadyExists =
                        cache.closedBricks.some(
                            cachedBrick =>
                                getRenkoBrickKey(
                                    cachedBrick
                                ) === brickKey
                        );

                    if (!alreadyExists) {
                        cache.closedBricks.push(
                            brick
                        );
                    }
                }

                // Mantém somente os últimos
                // 50 fechados no cache.
                if (
                    cache.closedBricks.length >
                    50
                ) {
                    cache.closedBricks =
                        cache.closedBricks.slice(
                            -50
                        );
                }

                cache.state =
                    data.state;

                const lastClosedBrick =
                    cache.closedBricks[
                        cache.closedBricks.length - 1
                    ];

                cache.latestClosedKey =
                    getRenkoBrickKey(
                        lastClosedBrick
                    );

                drawRenkoChart(
                    brickSize,
                    cache.closedBricks,
                    cache.state
                );
            }
        )
    );
}

/*
    INICIALIZAÇÃO
*/

loadSymbol();

updateDashboard();

loadRenkoCharts();


setInterval(
    updateDashboard,
    1000
);


setInterval(
    updateRenkoRealtime,
    250
);