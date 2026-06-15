import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Optional

import mt5_handler
from config import WEBHOOK_SECRET, HOST, PORT, DEFAULT_LOT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to MetaTrader 5...")
    if not mt5_handler.connect():
        logger.error("Cannot connect to MT5. Make sure MT5 terminal is running.")
    else:
        logger.info("MT5 connected successfully.")
    yield
    mt5_handler.disconnect()
    logger.info("MT5 disconnected.")


app = FastAPI(title="TradingView → MT5 Webhook", lifespan=lifespan)


class SignalPayload(BaseModel):
    token: str
    symbol: str
    action: str                          # buy | sell | close
    lot: Optional[float] = None
    sl: Optional[float] = Field(default=0.0)
    tp: Optional[float] = Field(default=0.0)
    comment: Optional[str] = "TradingView"


@app.post("/webhook")
async def webhook(payload: SignalPayload):
    # Xác thực token
    if payload.token != WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    lot = payload.lot if payload.lot is not None else DEFAULT_LOT

    logger.info(f"Signal received | {payload.action.upper()} {lot} {payload.symbol}")

    result = mt5_handler.place_order(
        symbol=payload.symbol,
        action=payload.action,
        lot=lot,
        sl=payload.sl or 0.0,
        tp=payload.tp or 0.0,
        comment=payload.comment,
    )

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result)

    return result


@app.get("/positions")
async def get_positions(symbol: Optional[str] = None):
    return mt5_handler.get_open_positions(symbol)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
