from fastapi import APIRouter, Header
from pydantic import BaseModel
import logging
from services.auth import signup, login, get_user

logger = logging.getLogger(__name__)
router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
async def auth_signup(req: AuthRequest):
    result = await signup(req.email, req.password)
    return result


@router.post("/login")
async def auth_login(req: AuthRequest):
    result = await login(req.email, req.password)
    return result


@router.get("/me")
async def auth_me(authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return {"error": "No token provided"}
    user = await get_user(token)
    if user:
        return user
    return {"error": "Invalid token"}
