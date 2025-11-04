# Placeholder routes for load testing
from fastapi import APIRouter

router = APIRouter(prefix="/loadtest", tags=["loadtest"])


@router.post("/run")
def run_loadtest_placeholder():
    return {"detail": "Not implemented"}
