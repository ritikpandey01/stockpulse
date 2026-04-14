from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from routes.analysis import router as analysis_router
from routes.sentiment import router as sentiment_router
from routes.recommendations import router as recommendations_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.history import router as history_router
from routes.market import router as market_router
from routes.fundamentals import router as fundamentals_router
from routes.screener import router as screener_router
from routes.comparison import router as comparison_router

app = FastAPI(title="StockPulse API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(analysis_router, prefix="/api")
app.include_router(sentiment_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(admin_router, prefix="/api/admin")
app.include_router(history_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(fundamentals_router, prefix="/api")
app.include_router(screener_router, prefix="/api")
app.include_router(comparison_router, prefix="/api")

# Serve frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/health")
async def health():
    return {"status": "ok", "service": "StockPulse", "version": "2.0.0"}
