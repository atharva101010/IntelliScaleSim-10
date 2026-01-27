from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
import logging

from app.database.session import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.container import Container, ContainerStatus
from app.schemas.container import (
    DeployContainerRequest,
    ContainerOut,
    ContainerListOut,
    ContainerActionResponse,
)
from app.services.docker_service import get_docker_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/containers", tags=["containers"])


def find_available_port(db: Session, start_port: int = 3000) -> int:
    """Find an available port starting from start_port"""
    used_ports = {c.port for c in db.query(Container.port).filter(Container.port.isnot(None)).all()}
    port = start_port
    while port in used_ports:
        port += 1
    return port




@router.get("/docker/status")
def get_docker_status(
    current_user: User = Depends(get_current_user),
):
    """Get Docker availability status for health checks."""
    docker_service = get_docker_service()
    return docker_service.get_docker_status()


@router.get("/docker/images")
def list_local_docker_images(
    current_user: User = Depends(get_current_user),
):
    """List all Docker images available locally in Docker Desktop."""
    docker_service = get_docker_service()
    images = docker_service.list_local_images()
    return {"images": images}


@router.post("/deploy", response_model=ContainerOut, status_code=status.HTTP_201_CREATED)
def deploy_container(
    payload: DeployContainerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deploy a real container from Docker Hub or build from GitHub."""
    
    # Check if container name already exists for this user
    existing = (
        db.query(Container)
        .filter(Container.user_id == current_user.id, Container.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Container with name '{payload.name}' already exists",
        )
    
    # Assign port if not provided
    assigned_port = payload.port if payload.port else find_available_port(db)
    
    # Initialize container record
    container = Container(
        user_id=current_user.id,
        name=payload.name,
        deployment_type=payload.deployment_type,
        port=assigned_port,
        cpu_limit=payload.cpu_limit,
        memory_limit=payload.memory_limit,
        environment_vars=payload.environment_vars or {},
        status=ContainerStatus.pending,
    )
    
    try:
        # Handle different deployment types
        if payload.deployment_type == "dockerhub":
            # Check Docker availability for Docker Hub deployments
            docker_service = get_docker_service()
            docker_status = docker_service.get_docker_status()
            
            if not docker_status['available']:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=docker_status['message']
                )
            
            # Docker Hub deployment
            image_name = payload.image
            if not image_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image name is required for Docker Hub deployments"
                )
            
            container.image = image_name
            container.source_url = image_name
            
            # Check if image exists locally first
            image_exists = docker_service.image_exists_locally(image_name)
            
            if not image_exists:
                # Image not found locally, pull from Docker Hub
                container.build_status = "pulling"
                # Save to DB first
                db.add(container)
                db.commit()
                db.refresh(container)
                
                logger.info(f"Image not found locally, pulling from Docker Hub: {image_name}")
                
                # Pull image with optional auth
                try:
                    docker_service.pull_image(
                        image_name=image_name,
                        username=payload.docker_username,
                        password=payload.docker_password
                    )
                    container.build_status = "success"
                except Exception as e:
                    container.build_status = "failed"
                    container.status = ContainerStatus.error
                    db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to pull image: {str(e)}"
                    )
            else:
                # Image found locally, skip pull
                logger.info(f"Using local image: {image_name}")
                container.build_status = "success"
                # Save to DB
                db.add(container)
                db.commit()
                db.refresh(container)
            
            # Run container
            logger.info(f"Running container: {container.name}")
            docker_container_id = docker_service.run_container(
                image=image_name,
                name=f"intelliscale-{container.id}-{container.name}",
                port=assigned_port,
                internal_port=payload.port or 80,  # Default to 80 if not specified
                cpu_limit=str(payload.cpu_limit / 1000),  # Convert millicores to cores
                mem_limit=f"{payload.memory_limit}m"
            )
            
            container.container_id = docker_container_id
            container.status = ContainerStatus.running
            container.started_at = datetime.now(timezone.utc)
            container.localhost_url = f"http://localhost:{assigned_port}"
            
            logger.info(f"Container deployed successfully: {container.name} at {container.localhost_url}")
            
        elif payload.deployment_type == "github":
            # GitHub deployment - clone repo, build image, deploy
            from ..services.git_service import get_git_service
            
            if not payload.source_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="GitHub repository URL(source_url) is required for GitHub deployments"
                )
            
            # Check Docker availability
            docker_service = get_docker_service()
            docker_status = docker_service.get_docker_status()
            
            if not docker_status['available']:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=docker_status['message']
                )
            
            git_service = get_git_service()
            repo_path = None
            
            # Add container to database early to get ID for image tagging
            db.add(container)
            db.flush()  # Get container.id without committing
            
            try:
                logger.info(f"Cloning GitHub repository: {payload.source_url}")
                # Clone repository
                repo_path = git_service.clone_repository(
                    repo_url=payload.source_url,
                    branch=payload.github_branch or "main",
                    token=payload.git_token
                )
                
                logger.info(f"Finding Dockerfile in repository")
                # Find Dockerfile
                dockerfile_path = git_service.find_dockerfile(
                    repo_path=repo_path,
                    dockerfile_path=payload.dockerfile_path
                )
                
                # Build context should be the directory containing the Dockerfile
                import os
                dockerfile_dir = os.path.dirname(dockerfile_path)
                build_context = dockerfile_dir if dockerfile_dir else repo_path
                
                # Generate unique image tag using container ID
                image_tag = f"intelliscale-github-{container.id}:latest"
                
                logger.info(f"Building Docker image: {image_tag}")
                logger.info(f"Build context: {build_context}")
                logger.info(f"Dockerfile: {dockerfile_path}")
                # Build image from Dockerfile
                docker_service.build_image_from_path(
                    build_context=build_context,
                    dockerfile_path=dockerfile_path,
                    image_tag=image_tag
                )
                
                # Update container with built image info
                container.image = image_tag
                container.source_url = payload.source_url
                container.build_status = "success"
                
                # Port already assigned earlier (line 74)
                logger.info(f"Container will use port: {assigned_port}")
                
                # Container already added to session earlier, just flush to ensure ID is available
                db.flush()
                
                # Detect internal port from Dockerfile EXPOSE directive
                internal_port = git_service.parse_dockerfile_expose(dockerfile_path)
                if not internal_port:
                    # Fallback to user-specified port or default 80
                    internal_port = payload.port or 80
                    logger.info(f"Using fallback internal port: {internal_port}")
                
                logger.info(f"Running container: {container.name}")
                logger.info(f"Port mapping: {assigned_port} (external) -> {internal_port} (internal)")
                # Run container
                docker_container_id = docker_service.run_container(
                    image=image_tag,
                    name=f"intelliscale-{container.id}-{container.name}",
                    port=assigned_port,
                    internal_port=internal_port,
                    cpu_limit=str(payload.cpu_limit / 1000),
                    mem_limit=f"{payload.memory_limit}m"
                )
                
                container.container_id = docker_container_id
                container.status = ContainerStatus.running
                container.started_at = datetime.now(timezone.utc)
                container.localhost_url = f"http://localhost:{assigned_port}"
                
                logger.info(f"GitHub deployment successful: {container.name} at {container.localhost_url}")
                
            except Exception as e:
                logger.error(f"GitHub deployment failed: {e}")
                container.build_status = "failed"
                container.status = ContainerStatus.error
                db.add(container)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"GitHub deployment failed: {str(e)}"
                )
            finally:
                # Always cleanup cloned repository
                if repo_path:
                    logger.info(f"Cleaning up repository at {repo_path}")
                    git_service.cleanup_repository(repo_path)
            
        elif payload.deployment_type == "simulated":
            # Keep old simulated behavior for backward compatibility
            container.image = payload.image or "simulated"
            container.status = ContainerStatus.running
            container.started_at = datetime.now(timezone.utc)
            db.add(container)  # Add container to session for simulated deployments
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid deployment_type: {payload.deployment_type}"
            )
        
        db.commit()
        db.refresh(container)
        return container
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        container.status = ContainerStatus.error
        if container.id:
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}"
        )


@router.get("", response_model=ContainerListOut)
def list_containers(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List containers. Students see only their own, teachers/admins see all."""
    
    query = db.query(Container)
    
    # Role-based filtering
    if current_user.role == UserRole.student:
        query = query.filter(Container.user_id == current_user.id)
    # Teachers and admins can see all containers
    
    # Status filtering
    if status_filter:
        try:
            status_enum = ContainerStatus(status_filter)
            query = query.filter(Container.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )
    
    # Order by newest first
    query = query.order_by(Container.created_at.desc())
    
    containers = query.all()
    
    return ContainerListOut(containers=containers, total=len(containers))


@router.get("/{container_id}", response_model=ContainerOut)
def get_container(
    container_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific container."""
    
    container = db.query(Container).filter(Container.id == container_id).first()
    
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )
    
    # Check ownership (students can only see their own)
    if current_user.role == UserRole.student and container.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this container",
        )
    
    return container


@router.post("/{container_id}/start", response_model=ContainerActionResponse)
def start_container(
    container_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a stopped container."""
    
    container = db.query(Container).filter(Container.id == container_id).first()
    
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )
    
    # Check ownership (students can only manage their own)
    if current_user.role == UserRole.student and container.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this container",
        )
    
    if container.status == ContainerStatus.running:
        return ContainerActionResponse(
            ok=True,
            message="Container is already running",
            container=container,
        )
    
    # Update container status
    container.status = ContainerStatus.running
    container.started_at = datetime.now(timezone.utc)
    container.stopped_at = None
    
    db.commit()
    db.refresh(container)
    
    return ContainerActionResponse(
        ok=True,
        message=f"Container '{container.name}' started successfully",
        container=container,
    )


@router.post("/{container_id}/stop", response_model=ContainerActionResponse)
def stop_container(
    container_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stop a running container."""
    
    container = db.query(Container).filter(Container.id == container_id).first()
    
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )
    
    # Check ownership
    if current_user.role == UserRole.student and container.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this container",
        )
    
    if container.status == ContainerStatus.stopped:
        return ContainerActionResponse(
            ok=True,
            message="Container is already stopped",
            container=container,
        )
    
    # Update container status
    container.status = ContainerStatus.stopped
    container.stopped_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(container)
    
    return ContainerActionResponse(
        ok=True,
        message=f"Container '{container.name}' stopped successfully",
        container=container,
    )


@router.delete("/{container_id}", response_model=ContainerActionResponse)
def delete_container(
    container_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a container."""
    
    container = db.query(Container).filter(Container.id == container_id).first()
    
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )
    
    # Check ownership
    if current_user.role == UserRole.student and container.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this container",
        )
    
    container_name = container.name
    db.delete(container)
    db.commit()
    
    return ContainerActionResponse(
        ok=True,
        message=f"Container '{container_name}' deleted successfully",
        container=None,
    )


@router.get("/{container_id}/logs")
def get_container_logs(
    container_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get simulated logs for a container."""
    
    container = db.query(Container).filter(Container.id == container_id).first()
    
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )
    
    # Check ownership
    if current_user.role == UserRole.student and container.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view logs for this container",
        )
    
    # Generate simulated logs based on container state
    logs = []
    if container.status == ContainerStatus.running:
        logs = [
            f"[{container.created_at.strftime('%Y-%m-%d %H:%M:%S')}] Container '{container.name}' initialized",
            f"[{container.started_at.strftime('%Y-%m-%d %H:%M:%S') if container.started_at else 'N/A'}] Starting {container.image}...",
            f"[{container.started_at.strftime('%Y-%m-%d %H:%M:%S') if container.started_at else 'N/A'}] Container started successfully",
            f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] Container is running with {container.cpu_limit}m CPU and {container.memory_limit}Mi memory",
            f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] Listening on port {container.port or 'N/A'}",
        ]
    elif container.status == ContainerStatus.stopped:
        logs = [
            f"[{container.created_at.strftime('%Y-%m-%d %H:%M:%S')}] Container '{container.name}' initialized",
            f"[{container.stopped_at.strftime('%Y-%m-%d %H:%M:%S') if container.stopped_at else 'N/A'}] Container stopped",
        ]
    else:
        logs = [
            f"[{container.created_at.strftime('%Y-%m-%d %H:%M:%S')}] Container '{container.name}' created",
            f"[{container.created_at.strftime('%Y-%m-%d %H:%M:%S')}] Status: {container.status.value}",
        ]
    
    return {"logs": logs, "container_name": container.name, "status": container.status.value}
