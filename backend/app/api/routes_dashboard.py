# Placeholder routes for dashboard and metrics
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
def get_metrics_placeholder():
    return {"metrics": {}}
