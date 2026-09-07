const statusDot =
    document.getElementById("status-dot");

const connectionStatus =
    document.getElementById("connection-status");

const mt5Status =
    document.getElementById("mt5-status");

const marketStatus =
    document.getElementById("market-status");

const lastTick =
    document.getElementById("last-tick");

const bid =
    document.getElementById("bid");

const ask =
    document.getElementById("ask");

const last =
    document.getElementById("last");

const spread =
    document.getElementById("spread");

const symbol =
    document.getElementById("symbol");

const description =
    document.getElementById("description");


function formatPrice(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "-";
    }

    return Number(value).toLocaleString(
        "pt-BR",
        {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }
    );
}


function setConnectionState(connected) {

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


function updateMarketStatus(timeMsc) {

    if (!timeMsc) {

        marketStatus.textContent =
            "SEM DADOS";

        marketStatus.className =
            "market-status market-offline";

        return;
    }

    const now =
        Date.now();

    const age =
        now - timeMsc;

    /*
        Por enquanto:
        tick com mais de 10 segundos
        é considerado STALE.

        Depois refinaremos isso,
        principalmente para mercado fechado.
    */

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
        date.toLocaleString("pt-BR");
}


async function loadSymbol() {

    try {

        const response =
            await fetch("/api/symbol");

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
            await fetch("/api/status");

        if (!response.ok) {

            setConnectionState(false);

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

        setConnectionState(false);

        console.error(
            "Erro status:",
            error
        );
    }
}


async function loadTick() {

    try {

        const response =
            await fetch("/api/tick");

        if (!response.ok) {
            return;
        }

        const data =
            await response.json();

        bid.textContent =
            formatPrice(data.bid);

        ask.textContent =
            formatPrice(data.ask);

        last.textContent =
            formatPrice(data.last);

        spread.textContent =
            formatPrice(data.spread);

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


async function updateDashboard() {

    await loadStatus();

    await loadTick();
}


loadSymbol();

updateDashboard();


setInterval(
    updateDashboard,
    1000
);