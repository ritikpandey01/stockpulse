from fastapi import APIRouter
import logging
from services.recommender import get_top_recommendations, get_sector_movers

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/recommendations")
async def recommendations(limit: int = 5):
    """Get top stock recommendations."""
    picks = get_top_recommendations(limit)
    sectors = get_sector_movers()
    return {
        "top_picks": picks,
        "sector_movers": sectors,
    }
