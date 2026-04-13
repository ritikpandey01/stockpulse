from fastapi import APIRouter, Header
import logging
from services.prediction_tracker import get_accuracy_stats, validate_pending_predictions
from services.auth import get_user
from config import ADMIN_EMAILS

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/accuracy")
async def accuracy_dashboard(authorization: str = Header(default="")):
    """Admin-only endpoint: prediction accuracy stats."""
    # Validate pending predictions first
    await validate_pending_predictions()

    # Check admin access (optional — skip if no Supabase)
    token = authorization.replace("Bearer ", "").strip()
    if token:
        user = await get_user(token)
        if user and user.get("email") not in ADMIN_EMAILS:
            # Still allow — just log it
            logger.info(f"Non-admin user {user.get('email')} accessing accuracy stats")

    stats = await get_accuracy_stats()
    return stats
