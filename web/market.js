const marketCfdButton =
    document.getElementById("market-cfd");

const marketWinButton =
    document.getElementById("market-win");


function setSelectedMarket(
    market
) {
    window.selectedMarket = market;

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