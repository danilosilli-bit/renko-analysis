async function apiGet(url, options = {}) {
    const response = await fetch(
        url,
        options
    );

    if (!response.ok) {
        return null;
    }

    return await response.json();
}


async function fetchSymbol() {
    return apiGet(
        "/api/symbol"
    );
}


async function fetchStatus() {
    return apiGet(
        "/api/status"
    );
}


async function fetchTick() {
    return apiGet(
        "/api/tick"
    );
}


function getRenkoBaseEndpoint(
    market
) {
    return market === "WIN"
        ? "/api/renko-win"
        : "/api/renko";
}


async function fetchRenko(
    market,
    brickSize
) {
    const baseEndpoint =
        getRenkoBaseEndpoint(
            market
        );

    return apiGet(
        `${baseEndpoint}/${brickSize}`
    );
}


async function fetchRenkoRealtime(
    market,
    brickSize
) {
    const baseEndpoint =
        getRenkoBaseEndpoint(
            market
        );

    return apiGet(
        `${baseEndpoint}/${brickSize}/realtime`,
        {
            cache: "no-store"
        }
    );
}

async function fetchWinOperations() {

    return apiGet(
        "/api/trading/win/operations",
        {
            cache: "no-store"
        }
    );
}


async function fetchCfdOperations() {

    return apiGet(
        "/api/trading/cfd/operations",
        {
            cache: "no-store"
        }
    );
}

async function fetchWinPositions() {
    return apiGet(
        "/api/trading/win/positions",
        {
            cache: "no-store"
        }
    );
}

async function fetchCfdPositions() {
    return apiGet(
        "/api/trading/cfd/positions",
        {
            cache: "no-store"
        }
    );
}

async function sendWinOrder(
    side,
    volume = 1,
    checkOnly = true
) {
    const response = await fetch(
        "/api/trading/win/order",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                side: side,
                volume: volume,
                check_only: checkOnly
            })
        }
    );

    if (!response.ok) {
        return null;
    }

    return await response.json();
}

async function closeWinPosition(
    operationId,
    checkOnly = true
) {

    const response = await fetch(
        "/api/trading/win/close-position",
        {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                operation_id:
                    operationId,
                check_only:
                    checkOnly
            })
        }
    );


    if (!response.ok) {

        throw new Error(
            "Erro ao fechar "
            + "operação WIN."
        );
    }


    return await response.json();
}

async function sendCfdOrder(
    side,
    volume = 0.05,
    checkOnly = true
) {
    const response = await fetch(
        "/api/trading/cfd/order",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                side: side,
                volume: volume,
                check_only: checkOnly
            })
        }
    );

    if (!response.ok) {
        return null;
    }

    return await response.json();
}

async function closeCfdPosition(
    operationId,
    checkOnly = true
) {

    const response = await fetch(
        "/api/trading/cfd/close-position",
        {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                operation_id:
                    operationId,
                check_only:
                    checkOnly
            })
        }
    );


    if (!response.ok) {

        throw new Error(
            "Erro ao fechar "
            + "operação CFD."
        );
    }


    return await response.json();
}

async function fetchWinTradingSignal() {
    return apiGet(
        "/api/trading-signal/win",
        {
            cache: "no-store"
        }
    );
}


async function fetchCfdTradingSignal() {
    return apiGet(
        "/api/trading-signal/cfd",
        {
            cache: "no-store"
        }
    );
}