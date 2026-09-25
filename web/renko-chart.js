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


