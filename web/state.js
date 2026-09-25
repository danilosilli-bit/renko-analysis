window.RENKO_SIZES =
    [10, 30, 45];


window.renkoChartCache = {
    CFD: {},
    WIN: {}
};


for (const market of ["CFD", "WIN"]) {

    for (
        const brickSize of
        window.RENKO_SIZES
    ) {

        window.renkoChartCache[
            market
        ][brickSize] = {
            closedBricks: [],
            state: null,
            latestClosedKey: null
        };
    }
}


window.getRenkoBrickKey =
    function (brick) {

        if (!brick) {
            return null;
        }

        return [
            brick.close_time,
            brick.open,
            brick.close
        ].join("|");
    };


window.selectedMarket = "CFD";