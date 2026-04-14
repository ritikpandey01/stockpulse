from fastapi import APIRouter
import logging
from services.fundamentals import get_fundamentals

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/fundamentals/{symbol}")
async def fundamentals(symbol: str):
    """Get comprehensive fundamental data for a stock."""
    symbol = symbol.upper().strip()
    data = get_fundamentals(symbol)
    return data
