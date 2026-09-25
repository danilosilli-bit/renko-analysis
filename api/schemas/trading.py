from pydantic import BaseModel


class MarketOrderRequest(BaseModel):
    side: str
    volume: float = 1
    check_only: bool = True


class ClosePositionRequest(BaseModel):
    ticket: int
    check_only: bool = True

