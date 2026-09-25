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

let lastMarketTickTime = null;
let lastMarketTickReceivedAt = null;


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

        lastMarketTickTime =
            null;

        lastMarketTickReceivedAt =
            null;

        return;
    }


    const now =
        Date.now();


    if (
        timeMsc !==
        lastMarketTickTime
    ) {

        lastMarketTickTime =
            timeMsc;

        lastMarketTickReceivedAt =
            now;
    }


    const age =
        lastMarketTickReceivedAt
            ? now -
              lastMarketTickReceivedAt
            : Infinity;


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
        new Date(
            lastMarketTickReceivedAt
        );


    lastTick.textContent =
        date.toLocaleString(
            "pt-BR"
        );
}


async function loadSymbol() {

    try {

        const data =
            await fetchSymbol();


        if (!data) {
            return;
        }


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

        const data =
            await fetchStatus();


        if (!data) {
            setConnectionState(false);
            return;
        }


        const xpStatus =
            document.getElementById(
                "xp-status"
            );

        const xpStatusDot =
            document.getElementById(
                "xp-status-dot"
            );


        const activtradesStatus =
            document.getElementById(
                "activtrades-status"
            );

        const activtradesStatusDot =
            document.getElementById(
                "activtrades-status-dot"
            );


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


        setConnectionState(
            connected
        );


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

        const data =
            await fetchTick();


        if (!data) {
            return;
        }


        const tick =
            selectedMarket === "WIN"
                ? data.win
                : data.cfd;


        if (!tick) {

            updateMarketStatus(
                null
            );

            return;
        }


        bid.textContent =
            formatPrice(
                tick.bid
            );


        ask.textContent =
            formatPrice(
                tick.ask
            );


        last.textContent =
            formatPrice(
                tick.last
            );


        spread.textContent =
            formatPrice(
                tick.spread
            );


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