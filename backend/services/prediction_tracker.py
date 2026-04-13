import logging
from datetime import datetime, timedelta
from services.database import get_supabase
from services.market_data import get_current_price

logger = logging.getLogger(__name__)


async def log_prediction(
    user_id: str | None,
    symbol: str,
    predicted_price: float,
    direction: str,
    timeframe: str,
) -> dict:
    """Log a prediction to the database for later accuracy validation."""
    sb = get_supabase()
    if not sb:
        return {"logged": False, "reason": "Database not configured"}

    # Calculate when to check
    now = datetime.utcnow()
    if timeframe == "5m":
        check_at = now + timedelta(minutes=5)
    elif timeframe == "15m":
        check_at = now + timedelta(minutes=15)
    elif timeframe == "1h":
        check_at = now + timedelta(hours=1)
    elif timeframe == "1d":
        check_at = now + timedelta(days=1)
    else:
        check_at = now + timedelta(minutes=5)

    try:
        data = {
            "user_id": user_id,
            "symbol": symbol,
            "predicted_price": predicted_price,
            "predicted_direction": direction,
            "result": "PENDING",
            "timeframe": timeframe,
            "check_at": check_at.isoformat(),
        }
        result = sb.table("predictions").insert(data).execute()
        return {"logged": True, "prediction_id": result.data[0]["id"] if result.data else None}
    except Exception as e:
        logger.error(f"Prediction log error: {e}")
        return {"logged": False, "reason": str(e)}


async def validate_pending_predictions():
    """Check pending predictions whose check_at time has passed. Run periodically."""
    sb = get_supabase()
    if not sb:
        return

    try:
        now = datetime.utcnow().isoformat()
        result = sb.table("predictions").select("*").eq("result", "PENDING").lte("check_at", now).execute()

        for pred in result.data or []:
            actual_price = get_current_price(pred["symbol"])
            if actual_price is None:
                continue

            # Determine actual direction
            if actual_price > pred["predicted_price"] * 0.998:  # small tolerance
                actual_direction = "UP"
            else:
                actual_direction = "DOWN"

            # Compare to predicted direction
            is_win = actual_direction == pred["predicted_direction"]

            sb.table("predictions").update({
                "actual_price": actual_price,
                "actual_direction": actual_direction,
                "result": "WIN" if is_win else "LOSS",
            }).eq("id", pred["id"]).execute()

            logger.info(f"Validated {pred['symbol']}: predicted {pred['predicted_direction']}, "
                        f"actual {actual_direction} → {'WIN' if is_win else 'LOSS'}")

    except Exception as e:
        logger.error(f"Validation error: {e}")


async def get_accuracy_stats() -> dict:
    """Get overall prediction accuracy statistics for admin dashboard."""
    sb = get_supabase()
    if not sb:
        return {"error": "Database not configured", "total": 0}

    try:
        all_preds = sb.table("predictions").select("*").neq("result", "PENDING").execute()
        data = all_preds.data or []

        total = len(data)
        wins = sum(1 for p in data if p["result"] == "WIN")
        losses = sum(1 for p in data if p["result"] == "LOSS")
        pending_result = sb.table("predictions").select("id", count="exact").eq("result", "PENDING").execute()
        pending = pending_result.count or 0

        # By timeframe
        by_timeframe = {}
        for p in data:
            tf = p.get("timeframe", "unknown")
            if tf not in by_timeframe:
                by_timeframe[tf] = {"total": 0, "wins": 0}
            by_timeframe[tf]["total"] += 1
            if p["result"] == "WIN":
                by_timeframe[tf]["wins"] += 1

        for tf in by_timeframe:
            bt = by_timeframe[tf]
            bt["accuracy"] = round(bt["wins"] / bt["total"] * 100, 1) if bt["total"] > 0 else 0

        return {
            "total_validated": total,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
            "by_timeframe": by_timeframe,
            "recent": data[-10:] if data else [],
        }
    except Exception as e:
        logger.error(f"Accuracy stats error: {e}")
        return {"error": str(e), "total": 0}
