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

        mt5Status.textContent =
            "CONNECTED";

    } else {

        statusDot.classList.remove(
            "online"
        );

        statusDot.classList.add(
            "offline"
        );

        connectionStatus.textContent =
            "OFFLINE";

        mt5Status.textContent =
            "DISCONNECTED";
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

function drawRenkoChart(
    brickSize,
    bricks
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

    const visibleBricks =
        bricks.slice(-50);


    countElement.textContent =
        `${visibleBricks.length} bricks`;


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
    const paddingBottom = 30;
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
            */

            if (
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

        const response =
            await fetch(
                "/api/status"
            );


        if (!response.ok) {

            setConnectionState(
                false
            );

            return;
        }


        const data =
            await response.json();


        const connected =
            data.mt5_connected === true &&
            data.terminal_connected === true;


        setConnectionState(
            connected
        );


    } catch (error) {

        setConnectionState(
            false
        );


        console.error(
            "Erro status:",
            error
        );
    }
}


async function loadTick() {

    try {

        const response =
            await fetch(
                "/api/tick"
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        if (
            data.status ===
            "WAITING_FOR_TICK"
        ) {

            updateMarketStatus(
                null
            );

            return;
        }


        bid.textContent =
            formatPrice(
                data.bid
            );


        ask.textContent =
            formatPrice(
                data.ask
            );


        last.textContent =
            formatPrice(
                data.last
            );


        spread.textContent =
            formatPrice(
                data.spread
            );


        updateMarketStatus(
            data.time_msc
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

        const response =
            await fetch(
                "/api/renko"
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        if (
            data.initialized !== true ||
            !data.renko
        ) {
            return;
        }


        RENKO_SIZES.forEach(
            brickSize => {

                updateRenkoPanel(
                    brickSize,
                    data.renko[
                        String(
                            brickSize
                        )
                    ]
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

        const response =
            await fetch(
                `/api/renko/${brickSize}`
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


        drawRenkoChart(
            brickSize,
            data.recent_bricks || []
        );


    } catch (error) {

        console.error(
            `Erro gráfico ${brickSize}R:`,
            error
        );
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


async function updateDashboard() {

    await Promise.all([

        loadStatus(),

        loadTick(),

        loadRenkoPanels(),

        loadRenkoCharts()

    ]);
}


/*
    INICIALIZAÇÃO
*/

loadSymbol();

updateDashboard();


setInterval(
    updateDashboard,
    1000
);