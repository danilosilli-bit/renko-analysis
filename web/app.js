async function loadRenkoPanels() {

    try {

        const dataList =
            await Promise.all(

                RENKO_SIZES.map(
                    brickSize =>
                        fetchRenko(
                            selectedMarket,
                            brickSize
                        )
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

        const data =
            await fetchRenko(
                selectedMarket,
                brickSize
            );


        if (!data) {
            return;
        }


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

        const data =
            await fetchRenkoRealtime(
                selectedMarket,
                brickSize
            );


        if (!data) {
            return null;
        }


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

let currentWinPositionTicket = null;
let currentCfdPositionTicket = null;

async function loadTradingPosition() {

    try {

        const selectedMarket =
            window.selectedMarket;

        let data;

        if (selectedMarket === "CFD") {

            data =
                await fetchCfdPositions();

        } else if (selectedMarket === "WIN") {

            data =
                await fetchWinPositions();

        } else {

            console.error(
                "Mercado inválido para posição:",
                selectedMarket
            );

            return;
        }


        if (
            !data ||
            data.status !== "OK"
        ) {
            return;
        }


        const positions =
            data.positions || [];


        const statusElement =
            document.getElementById(
                "win-position-status"
            );

        const sideElement =
            document.getElementById(
                "win-position-side"
            );

        const volumeElement =
            document.getElementById(
                "win-position-volume"
            );

        const priceElement =
            document.getElementById(
                "win-position-price"
            );

        const profitElement =
            document.getElementById(
                "win-position-profit"
            );

        const buyButton =
            document.getElementById(
                "win-buy-button"
            );

        const sellButton =
            document.getElementById(
                "win-sell-button"
            );

        const closeButton =
            document.getElementById(
                "win-close-button"
            );


        if (positions.length === 0) {

            if (selectedMarket === "CFD") {

                currentCfdPositionTicket =
                    null;

            } else {

                currentWinPositionTicket =
                    null;
            }


            statusElement.textContent =
                "FLAT";

            sideElement.textContent =
                "-";

            volumeElement.textContent =
                "0";

            priceElement.textContent =
                "-";

            profitElement.textContent =
                "-";


            if (buyButton) {
                buyButton.disabled = false;
            }

            if (sellButton) {
                sellButton.disabled = false;
            }

            if (closeButton) {
                closeButton.disabled = true;
            }

            return;
        }


        const position =
            positions[0];


        if (selectedMarket === "CFD") {

            currentCfdPositionTicket =
                position.ticket;

        } else {

            currentWinPositionTicket =
                position.ticket;
        }


        statusElement.textContent =
            "ABERTA";

        sideElement.textContent =
            position.type === 0
                ? "COMPRA"
                : "VENDA";

        volumeElement.textContent =
            position.volume;

        priceElement.textContent =
            position.price_open;

        profitElement.textContent =
            position.profit;


        if (buyButton) {
            buyButton.disabled = false;
        }

        if (sellButton) {
            sellButton.disabled = false;
        }

        if (closeButton) {
            closeButton.disabled = false;
        }

    } catch (error) {

        console.error(
            "Erro posição:",
            error
        );
    }
}
/*
    ATUALIZAÇÃO GERAL DO DASHBOARD
*/

async function updateDashboard() {

    await Promise.all([

        loadStatus(),

        loadTick(),

        loadRenkoPanels(),

        loadTradingPosition()

    ]);
}


/*
    ATUALIZAÇÃO DOS GRÁFICOS RENKO
*/

let renkoRealtimeLoading = false;

async function updateRenkoRealtime() {


    if (renkoRealtimeLoading) {
        return;
    }

    renkoRealtimeLoading = true;

    try {
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

                    /*
                        O endpoint realtime devolve todos
                        os bricks acumulados no runtime.

                        Adicionamos somente os que ainda
                        não existem no cache.
                    */
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

                    /*
                        IMPORTANTE:

                        Como o cache mantém apenas 50
                        bricks, bricks antigos do runtime
                        podem ser recebidos novamente.

                        Ordenamos por close_time antes
                        de cortar o cache para impedir
                        que esses bricks antigos apareçam
                        no final do gráfico.
                    */
                    cache.closedBricks.sort(
                        (a, b) =>
                            Number(
                                a.close_time
                            ) -
                            Number(
                                b.close_time
                            )
                    );

                    // Mantém somente os últimos
                    // 50 bricks fechados.
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
    } finally {
        renkoRealtimeLoading = false;
    }
}

async function checkWinBuyOrder() {

    const buyButton =
        document.getElementById(
            "win-buy-button"
        );

    if (!buyButton) {
        return;
    }

    buyButton.disabled = true;

    try {

        const selectedMarket =
            window.selectedMarket;

        let result;

        if (
            selectedMarket === "CFD"
        ) {

            result =
                await sendCfdOrder(
                    "BUY",
                    0.05,
                    false
                );

            console.log(
                "CFD BUY:",
                result
            );

        } else if (
            selectedMarket === "WIN"
        ) {

            result =
                await sendWinOrder(
                    "BUY",
                    1,
                    false
                );

            console.log(
                "WIN BUY:",
                result
            );

        } else {

            throw new Error(
                "Mercado não selecionado. "
                + "Ordem bloqueada."
            );
        }

        await loadTradingPosition();

    } catch (error) {

        console.error(
            "Erro BUY:",
            error
        );

    } finally {

        buyButton.disabled = false;
    }
}

async function checkWinSellOrder() {

    const sellButton =
        document.getElementById(
            "win-sell-button"
        );

    if (!sellButton) {
        return;
    }

    sellButton.disabled = true;

    try {

        const selectedMarket =
            window.selectedMarket;

        let result;

        if (
            selectedMarket === "CFD"
        ) {

            result =
                await sendCfdOrder(
                    "SELL",
                    0.05,
                    false
                );

            console.log(
                "CFD SELL:",
                result
            );

        } else if (
            selectedMarket === "WIN"
        ) {

            result =
                await sendWinOrder(
                    "SELL",
                    1,
                    false
                );

            console.log(
                "WIN SELL:",
                result
            );

        } else {

            throw new Error(
                "Mercado não selecionado. "
                + "Ordem bloqueada."
            );
        }

        await loadTradingPosition();

    } catch (error) {

        console.error(
            "Erro SELL:",
            error
        );

    } finally {

        sellButton.disabled = false;
    }
}

async function checkWinClosePosition() {

    const selectedMarket =
        window.selectedMarket;

    let positionTicket = null;

    if (selectedMarket === "CFD") {

        positionTicket =
            currentCfdPositionTicket;

    } else if (selectedMarket === "WIN") {

        positionTicket =
            currentWinPositionTicket;

    } else {

        console.error(
            "Mercado não selecionado. "
            + "Fechamento bloqueado."
        );

        return;
    }


    if (!positionTicket) {

        console.log(
            "Nenhuma posição "
            + selectedMarket
            + " para fechar."
        );

        return;
    }


    const closeButton =
        document.getElementById(
            "win-close-button"
        );

    if (!closeButton) {
        return;
    }


    closeButton.disabled = true;


    try {

        let result;

        if (selectedMarket === "CFD") {

            result =
                await closeCfdPosition(
                    positionTicket,
                    false
                );

            console.log(
                "CFD CLOSE:",
                result
            );

        } else {

            result =
                await closeWinPosition(
                    positionTicket,
                    false
                );

            console.log(
                "WIN CLOSE:",
                result
            );
        }


        await loadTradingPosition();


    } catch (error) {

        console.error(
            "Erro CLOSE:",
            error
        );

    } finally {

        closeButton.disabled = false;
    }
}

/*
    INICIALIZAÇÃO
*/

loadSymbol();

updateDashboard();

loadRenkoCharts();

const winBuyButton =
    document.getElementById(
        "win-buy-button"
    );

if (winBuyButton) {

    winBuyButton.disabled = false;

    winBuyButton.addEventListener(
        "click",
        checkWinBuyOrder
    );
}

const winSellButton =
    document.getElementById(
        "win-sell-button"
    );

if (winSellButton) {

    winSellButton.disabled = false;

    winSellButton.addEventListener(
        "click",
        checkWinSellOrder
    );
}

const winCloseButton =
    document.getElementById(
        "win-close-button"
    );

if (winCloseButton) {

    winCloseButton.disabled = false;

    winCloseButton.addEventListener(
        "click",
        checkWinClosePosition
    );
}

setInterval(
    updateDashboard,
    1000
);


setInterval(
    updateRenkoRealtime,
    250
);


