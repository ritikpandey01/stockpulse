from fastapi import APIRouter
import logging
from services.news_sentiment import get_full_sentiment
from services.market_data import get_stock_info

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    """Get news sentiment analysis for a stock."""
    symbol = symbol.upper().strip()
    info = get_stock_info(symbol)
    result = await get_full_sentiment(symbol, info.get("name", ""))
    result["symbol"] = symbol
    result["company"] = info.get("name", symbol)
    return result
