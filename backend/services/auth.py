import logging
from services.database import get_supabase, is_supabase_configured

logger = logging.getLogger(__name__)


async def signup(email: str, password: str) -> dict:
    """Create a new user account."""
    sb = get_supabase()
    if not sb:
        return {"error": "Database not configured. Please add Supabase credentials to .env"}
    try:
        result = sb.auth.sign_up({"email": email, "password": password})
        if result.session:
            return {
                "user_id": result.user.id,
                "email": result.user.email,
                "access_token": result.session.access_token,
            }
        elif result.user:
            return {"message": "Signup successful! Please check your email to confirm, then Login."}
        return {"error": "Signup failed"}
    except Exception as e:
        return {"error": str(e)}


async def login(email: str, password: str) -> dict:
    """Login and return session."""
    sb = get_supabase()
    if not sb:
        return {"error": "Database not configured"}
    try:
        result = sb.auth.sign_in_with_password({"email": email, "password": password})
        if result.user and result.session:
            return {
                "user_id": result.user.id,
                "email": result.user.email,
                "access_token": result.session.access_token,
            }
        return {"error": "Invalid credentials"}
    except Exception as e:
        return {"error": str(e)}


async def get_user(token: str) -> dict | None:
    """Verify token and return user info."""
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.auth.get_user(token)
        if result.user:
            return {"user_id": result.user.id, "email": result.user.email}
        return None
    except Exception:
        return None
