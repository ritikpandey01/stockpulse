from fastapi import APIRouter
from pydantic import BaseModel
import logging
from services.comparison import compare_stocks

logger = logging.getLogger(__name__)
router = APIRouter()


class CompareRequest(BaseModel):
    symbols: list[str]
    period: str = "3mo"
    interval: str = "1d"


@router.post("/compare")
async def compare(req: CompareRequest):
    """Compare multiple stocks side by side."""
    try:
        result = compare_stocks(req.symbols, req.period, req.interval)
        return result
    except Exception as e:
        logger.error(f"Compare error: {e}")
        return {"error": str(e)}
