# Placeholder routes for billing simulation
from fastapi import APIRouter

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/simulate")
def simulate_billing_placeholder():
    return {"detail": "Not implemented"}
