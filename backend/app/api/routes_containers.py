# Placeholder routes for container management
from fastapi import APIRouter

router = APIRouter(prefix="/containers", tags=["containers"])


@router.post("/deploy")
def deploy_container_placeholder():
    return {"detail": "Not implemented"}


@router.get("/list")
def list_containers_placeholder():
    return {"containers": []}
