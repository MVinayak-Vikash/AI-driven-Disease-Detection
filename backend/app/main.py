from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.utils.logger import setup_logger
from backend.app.api.routes import (
    auth_router,
    profile_router,
    devices_router,
    sessions_router,
    readings_router,
    signal_router,
    assessment_router,
    history_router,
    ws_router
)

logger = setup_logger("cardionav.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 65)
    logger.info(f"🫀 {settings.APP_NAME} (v{settings.APP_VERSION}) Starting")
    logger.info(f"🤖 AI Provider: {settings.AI_PROVIDER.upper()}")
    logger.info(f"🌐 Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 65)
    yield
    logger.info("CardioNav AI backend shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Clinical Decision-Support Screening Platform with Multi-Modal Sensor Fusion & AI Risk Referral.",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(devices_router)
app.include_router(sessions_router)
app.include_router(readings_router)
app.include_router(signal_router)
app.include_router(assessment_router)
app.include_router(history_router)
app.include_router(ws_router)

@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "ai_provider": settings.AI_PROVIDER
    }
