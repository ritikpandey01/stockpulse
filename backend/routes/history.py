from fastapi import APIRouter, Header
import logging
from services.database import get_supabase
from services.auth import get_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/history")
async def get_history(authorization: str = Header(default="")):
    """Get user's search/analysis history."""
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return {"error": "Authentication required", "history": []}

    user = await get_user(token)
    if not user:
        return {"error": "Invalid token", "history": []}

    sb = get_supabase()
    if not sb:
        return {"history": [], "message": "Database not configured"}

    try:
        result = sb.table("search_history").select("*").eq(
            "user_id", user["user_id"]
        ).order("created_at", desc=True).limit(50).execute()
        return {"history": result.data or []}
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return {"history": [], "error": str(e)}


@router.post("/history")
async def save_history(data: dict, authorization: str = Header(default="")):
    """Save a search to user history."""
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return {"saved": False}

    user = await get_user(token)
    if not user:
        return {"saved": False}

    sb = get_supabase()
    if not sb:
        return {"saved": False}

    try:
        sb.table("search_history").insert({
            "user_id": user["user_id"],
            "symbol": data.get("symbol", ""),
            "analysis_type": data.get("analysis_type", "full"),
            "result_summary": data.get("summary", {}),
        }).execute()
        return {"saved": True}
    except Exception as e:
        logger.error(f"History save error: {e}")
        return {"saved": False}
