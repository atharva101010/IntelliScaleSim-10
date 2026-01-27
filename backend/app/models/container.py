from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum
from datetime import datetime
from sqlalchemy import func


class ContainerStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    stopped = "stopped"
    error = "error"


class Container(Base):
    __tablename__ = "containers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=True)  # Nullable for GitHub builds
    status: Mapped[ContainerStatus] = mapped_column(
        Enum(ContainerStatus), nullable=False, default=ContainerStatus.pending
    )
    port: Mapped[int] = mapped_column(Integer, nullable=True)
    cpu_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=500)  # millicores
    memory_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=512)  # MB
    environment_vars: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # New fields for real deployments
    deployment_type: Mapped[str] = mapped_column(String(20), nullable=True)  # 'github' or 'dockerhub' or 'simulated'
    source_url: Mapped[str] = mapped_column(Text, nullable=True)  # GitHub URL or Docker image name
    build_status: Mapped[str] = mapped_column(String(20), nullable=True)  # 'pending', 'building', 'success', 'failed'
    build_logs: Mapped[str] = mapped_column(Text, nullable=True)  # Build output
    container_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Real Docker container ID
    localhost_url: Mapped[str] = mapped_column(String(500), nullable=True)  # http://localhost:PORT
    public_url: Mapped[str] = mapped_column(String(500), nullable=True)  # Optional ngrok/public URL

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    load_tests = relationship("LoadTest", back_populates="container")

