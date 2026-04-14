from fastapi import APIRouter
import logging
from services.market_overview import get_market_overview

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/market/overview")
async def market_overview():
    """Get full market overview: indices, sectors, fear/greed."""
    try:
        data = get_market_overview()
        return data
    except Exception as e:
        logger.error(f"Market overview error: {e}")
        return {"indices": [], "sectors": [], "fear_greed": {"score": 50, "label": "Neutral", "factors": []}}
