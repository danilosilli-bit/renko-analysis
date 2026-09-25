from fastapi import APIRouter

from api.schemas.trading import (
    ClosePositionRequest,
    MarketOrderRequest,
)

from trading.trading_service import (
    TradingService,
)


router = APIRouter(
    prefix="/api/trading",
    tags=["trading"],
)


_trading_service = None


def configure_trading_router(
    trading_service: TradingService,
):
    global _trading_service

    _trading_service = trading_service


def get_trading_service():

    if _trading_service is None:
        raise RuntimeError(
            "TradingService não configurado."
        )

    return _trading_service


@router.post("/win/order")
def send_win_order(
    order: MarketOrderRequest,
):

    service = get_trading_service()

    return service.send_market_order(
        side=order.side,
        volume=order.volume,
        check_only=order.check_only,
        broker_id="xp",
    )


@router.get("/win/positions")
def get_win_positions():

    service = get_trading_service()

    return service.get_positions()


@router.post("/win/close-position")
def close_win_position(
    request: ClosePositionRequest,
):

    service = get_trading_service()

    return service.close_position(
        ticket=request.ticket,
        check_only=request.check_only,
        broker_id="xp",
    )

@router.get("/cfd/positions")
def get_cfd_positions():

    service = get_trading_service()

    return service.get_positions(
        broker_id="activtrades"
    )

@router.post("/cfd/order")
def send_cfd_order(
    order: MarketOrderRequest,
):

    service = get_trading_service()

    return service.send_market_order(
        side=order.side,
        volume=order.volume,
        check_only=order.check_only,
        broker_id="activtrades",
    )

@router.post("/cfd/close-position")
def close_cfd_position(
    request: ClosePositionRequest,
):

    service = get_trading_service()

    return service.close_position(
        ticket=request.ticket,
        check_only=request.check_only,
        broker_id="activtrades",
    )