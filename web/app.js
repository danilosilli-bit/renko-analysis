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
            closeButton.disabled = true;
        }

    } catch (error) {

        console.error(
            "Erro posição:",
            error
        );
    }
}

async function loadTradingSignal() {

    try {

        const marketAtRequest =
            window.selectedMarket;

        let data;

        if (marketAtRequest === "CFD") {

            data =
                await fetchCfdTradingSignal();

        } else if (marketAtRequest === "WIN") {

            data =
                await fetchWinTradingSignal();

        } else {

            return;
        }


        /*
            Se o mercado mudou enquanto
            aguardávamos a resposta,
            ignoramos a resposta antiga.
        */
        if (
            marketAtRequest !==
            window.selectedMarket
        ) {
            return;
        }


        if (!data) {
            return;
        }


        const directionElement =
            document.getElementById(
                "trading-signal-direction"
            );

        const buyElement =
            document.getElementById(
                "trading-signal-buy"
            );

        const sellElement =
            document.getElementById(
                "trading-signal-sell"
            );

        const maxStopElement =
            document.getElementById(
                "trading-signal-max-stop"
            );


        if (
            !directionElement ||
            !buyElement ||
            !sellElement ||
            !maxStopElement
        ) {
            return;
        }


        if (!data.ready) {

            directionElement.textContent = "-";
            buyElement.textContent = "-";
            sellElement.textContent = "-";
            maxStopElement.textContent = "-";

            return;
        }


        directionElement.textContent =
            data.direction === "BUY"
                ? "COMPRA"
                : "VENDA";

        buyElement.textContent =
            data.can_buy === true
                ? "PERMITIDA"
                : "BLOQUEADA";

        sellElement.textContent =
            data.can_sell === true
                ? "PERMITIDA"
                : "BLOQUEADA";

        maxStopElement.textContent =
            data.max_stop_price ?? "-";


    } catch (error) {

        console.error(
            "Erro sinal operacional 30R:",
            error
        );
    }
}

async function loadTradingOperations() {

    try {

        const marketAtRequest =
            window.selectedMarket;

        let data;

        if (marketAtRequest === "CFD") {

            data =
                await fetchCfdOperations();

        } else if (
            marketAtRequest === "WIN"
        ) {

            data =
                await fetchWinOperations();

        } else {

            return;
        }


        if (
            marketAtRequest !==
            window.selectedMarket
        ) {
            return;
        }


        if (
            !data ||
            data.status !== "OK"
        ) {
            return;
        }


        const operations =
            data.operations || [];

        const listElement =
            document.getElementById(
                "trading-operations-list"
            );

        if (!listElement) {
            return;
        }


        listElement.innerHTML = "";


        if (operations.length === 0) {

            const emptyRow =
                document.createElement(
                    "div"
                );

            emptyRow.className =
                "position-row";

            const emptyLabel =
                document.createElement(
                    "span"
                );

            emptyLabel.className =
                "position-label";

            emptyLabel.textContent =
                "Nenhuma operação aberta";

            emptyRow.appendChild(
                emptyLabel
            );

            listElement.appendChild(
                emptyRow
            );

            return;
        }


        for (
            const operation
            of operations
        ) {

            const operationBlock =
                document.createElement(
                    "div"
                );


            const sideRow =
                document.createElement(
                    "div"
                );

            sideRow.className =
                "position-row";

            const sideLabel =
                document.createElement(
                    "span"
                );

            sideLabel.className =
                "position-label";

            sideLabel.textContent =
                "Operação";

            const sideValue =
                document.createElement(
                    "span"
                );

            sideValue.className =
                "position-value";

            sideValue.textContent =
                (
                    operation.side
                    + " | "
                    + operation.volume
                );

            sideRow.appendChild(
                sideLabel
            );

            sideRow.appendChild(
                sideValue
            );


            const priceRow =
                document.createElement(
                    "div"
                );

            priceRow.className =
                "position-row";

            const priceLabel =
                document.createElement(
                    "span"
                );

            priceLabel.className =
                "position-label";

            priceLabel.textContent =
                "Entrada";

            const priceValue =
                document.createElement(
                    "span"
                );

            priceValue.className =
                "position-value";

            priceValue.textContent =
                (
                    operation.entry_price
                    ?? "-"
                );

            priceRow.appendChild(
                priceLabel
            );

            priceRow.appendChild(
                priceValue
            );


            const stopRow =
                document.createElement(
                    "div"
                );

            stopRow.className =
                "position-row";

            const stopLabel =
                document.createElement(
                    "span"
                );

            stopLabel.className =
                "position-label";

            stopLabel.textContent =
                "Stop máx.";

            const stopValue =
                document.createElement(
                    "span"
                );

            stopValue.className =
                "position-value";

            stopValue.textContent =
                operation.max_stop_price;

            stopRow.appendChild(
                stopLabel
            );

            stopRow.appendChild(
                stopValue
            );


            const closeRow =
                document.createElement(
                    "div"
                );

            closeRow.className =
                "position-row";


            const closeButton =
                document.createElement(
                    "button"
                );

            closeButton.className =
                "trade-button close-button";

            closeButton.textContent =
                "FECHAR ESTA OPERAÇÃO";


            closeButton.addEventListener(
                "click",
                async () => {

                    const confirmationMessage =
                        "Confirmar fechamento?\n\n"
                        + "Mercado: "
                        + operation.feed
                        + "\n"
                        + "Lado: "
                        + operation.side
                        + "\n"
                        + "Volume: "
                        + operation.volume
                        + "\n"
                        + "Operation ID: "
                        + operation.operation_id;


                    const confirmed =
                        window.confirm(
                            confirmationMessage
                        );


                    if (!confirmed) {
                        return;
                    }


                    closeButton.disabled =
                        true;


                    try {

                        let result;

                        if (
                            operation.feed
                            === "CFD"
                        ) {

                            result =
                                await closeCfdPosition(
                                    operation.operation_id,
                                    false
                                );

                        } else if (
                            operation.feed
                            === "WIN"
                        ) {

                            result =
                                await closeWinPosition(
                                    operation.operation_id,
                                    false
                                );

                        } else {

                            throw new Error(
                                "Feed inválido "
                                + "na operação."
                            );
                        }


                        console.log(
                            "CLOSE OPERATION:",
                            result
                        );


                        await Promise.all([
                            loadTradingOperations(),
                            loadTradingPosition()
                        ]);


                    } catch (error) {

                        console.error(
                            "Erro ao fechar operação:",
                            error
                        );

                    } finally {

                        closeButton.disabled =
                            false;
                    }
                }
            );


            closeRow.appendChild(
                closeButton
            );


            operationBlock.appendChild(
                sideRow
            );

            operationBlock.appendChild(
                priceRow
            );

            operationBlock.appendChild(
                stopRow
            );

            operationBlock.appendChild(
                closeRow
            );


            listElement.appendChild(
                operationBlock
            );
        }


    } catch (error) {

        console.error(
            "Erro ao carregar operações:",
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

        loadTradingPosition(),

        loadTradingSignal(),

        loadTradingOperations()

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
    winCloseButton.disabled = true;
}

setInterval(
    updateDashboard,
    1000
);


setInterval(
    updateRenkoRealtime,
    250
);


