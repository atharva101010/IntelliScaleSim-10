from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class ContainerStatusEnum(str, Enum):
    pending = "pending"
    running = "running"
    stopped = "stopped"
    error = "error"


class DeployContainerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Container name")
    deployment_type: str = Field(..., description="Deployment type: 'github', 'dockerhub', or 'simulated'")
    
    # For GitHub deployments
    source_url: Optional[str] = Field(None, description="GitHub repository URL or Docker image name")
    git_username: Optional[str] = Field(None, description="GitHub username (for private repos)")
    git_token: Optional[str] = Field(None, description="GitHub personal access token (for private repos)")
    github_branch: Optional[str] = Field("main", description="GitHub branch to clone (default: main)")
    dockerfile_path: Optional[str] = Field(None, description="Path to Dockerfile in repo (auto-detect if None)")
    
    # For Docker Hub deployments
    image: Optional[str] = Field(None, description="Docker image (e.g., nginx:latest)")
    docker_username: Optional[str] = Field(None, description="Docker Hub username (for private images)")
    docker_password: Optional[str] = Field(None, description="Docker Hub password (for private images)")
    
    # Common fields
    port: Optional[int] = Field(None, ge=1, le=65535, description="Exposed port (auto-detect if None)")
    cpu_limit: int = Field(500, ge=100, le=4000, description="CPU limit in millicores (100-4000)")
    memory_limit: int = Field(512, ge=128, le=8192, description="Memory limit in MB (128-8192)")
    environment_vars: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError('Name can only contain alphanumeric characters, hyphens, and underscores')
        return v


class ContainerOut(BaseModel):
    id: int
    user_id: int
    name: str
    image: Optional[str] = None  # Nullable for GitHub builds in progress
    status: ContainerStatusEnum
    port: Optional[int]
    cpu_limit: int
    memory_limit: int
    environment_vars: Dict[str, str]
    
    # Deployment fields
    deployment_type: Optional[str] = None
    source_url: Optional[str] = None
    build_status: Optional[str] = None
    container_id: Optional[str] = None
    localhost_url: Optional[str] = None
    public_url: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContainerListOut(BaseModel):
    containers: list[ContainerOut]
    total: int


class ContainerActionResponse(BaseModel):
    ok: bool
    message: str
    container: Optional[ContainerOut] = None
