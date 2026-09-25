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