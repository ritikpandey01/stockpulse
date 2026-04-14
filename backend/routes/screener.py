from fastapi import APIRouter, Query
import logging
from services.screener import screen_stocks

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/screener")
async def screener(
    sector: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    min_market_cap: float = Query(None),
    min_pe: float = Query(None),
    max_pe: float = Query(None),
    min_rsi: float = Query(None),
    max_rsi: float = Query(None),
    signal: str = Query(None),
    sort_by: str = Query("score"),
    limit: int = Query(20),
):
    """Screen stocks with customizable filters."""
    try:
        results = screen_stocks(
            sector=sector,
            min_price=min_price,
            max_price=max_price,
            min_market_cap=min_market_cap,
            min_pe=min_pe,
            max_pe=max_pe,
            min_rsi=min_rsi,
            max_rsi=max_rsi,
            signal_filter=signal,
            sort_by=sort_by,
            limit=limit,
        )
        return {"results": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Screener error: {e}")
        return {"results": [], "total": 0, "error": str(e)}
