from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_auth, routes_containers, routes_loadtest, routes_dashboard, routes_monitoring, routes_autoscaling
from app.models.base import Base
from app.database.session import engine
from app.database.init_db import ensure_columns
import logging
import asyncio

# Load Testing feature enabled
app = FastAPI(title="IntelliScaleSim API", version="0.1.0")

# CORS (adjust origins via env in future)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "IntelliScaleSim API", "status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}

# Include routers
app.include_router(routes_auth.router)
app.include_router(routes_containers.router)
app.include_router(routes_loadtest.router)
app.include_router(routes_dashboard.router)
app.include_router(routes_monitoring.router)
app.include_router(routes_autoscaling.router)  # Auto-scaling API

logger = logging.getLogger(__name__)


# Background task for auto-scaling
async def autoscaler_background_task():
    """Background task that evaluates scaling policies every 30 seconds"""
    from app.services.autoscaler_service import AutoScalerService
    from app.services.docker_service import DockerService
    from app.database.session import SessionLocal
    
    logger.info("🚀 Auto-scaler background task started")
    
    while True:
        try:
            await asyncio.sleep(30)  # Every 30 seconds
            
            # Create new session for this iteration
            db = SessionLocal()
            docker_service = DockerService()
            autoscaler = AutoScalerService(db, docker_service)
            
            logger.info("🔍 Evaluating auto-scaling policies...")
            autoscaler.evaluate_all_policies()
            
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Error in autoscaler background task: {e}", exc_info=True)


@app.on_event("startup")
async def on_startup():
    # Create tables
    Base.metadata.create_all(bind=engine)
    ensure_columns(engine)
    
    logger.info("========================================")
    logger.info("📊 Starting auto-scaler background task...")
    logger.info("========================================")
    
    # Start auto-scaler background task
    asyncio.create_task(autoscaler_background_task())
    
    logger.info("✅ Application startup complete")
