# Placeholder routes for autoscaling simulation
from fastapi import APIRouter

router = APIRouter(prefix="/autoscale", tags=["autoscale"])


@router.post("/configure")
def configure_autoscale_placeholder():
    return {"detail": "Not implemented"}
