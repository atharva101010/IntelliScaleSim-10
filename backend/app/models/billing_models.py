from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, DECIMAL, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from datetime import datetime
from sqlalchemy import func
import enum


class PricingProvider(str, enum.Enum):
    """Cloud provider pricing models"""
    aws = "aws"
    gcp = "gcp"
    azure = "azure"


class ResourceQuota(Base):
    """Define resource quotas/limits for containers"""
    __tablename__ = "resource_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    container_id: Mapped[int] = mapped_column(Integer, ForeignKey("containers.id"), nullable=False, index=True)
    
    # Resource limits
    cpu_cores: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)  # vCPU cores
    memory_gb: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)  # GB
    storage_gb: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)  # GB
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ResourceUsage(Base):
    """Track actual resource consumption over time"""
    __tablename__ = "resource_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    container_id: Mapped[int] = mapped_column(Integer, ForeignKey("containers.id"), nullable=False, index=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Resource metrics
    cpu_percent: Mapped[float] = mapped_column(Float, nullable=False)  # CPU usage percentage
    cpu_cores_used: Mapped[float] = mapped_column(Float, nullable=True)  # Actual cores used
    memory_mb: Mapped[float] = mapped_column(Float, nullable=False)  # Memory in MB
    memory_gb: Mapped[float] = mapped_column(Float, nullable=True)  # Memory in GB
    storage_mb: Mapped[float] = mapped_column(Float, nullable=True)  # Storage in MB
    storage_gb: Mapped[float] = mapped_column(Float, nullable=True)  # Storage in GB
    
    # Network metrics (optional)
    network_rx_bytes: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    network_tx_bytes: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    
    # Request metrics (from load tests)
    requests_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)


class BillingSnapshot(Base):
    """Store calculated billing data at intervals"""
    __tablename__ = "billing_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    container_id: Mapped[int] = mapped_column(Integer, ForeignKey("containers.id"), nullable=False, index=True)
    
    provider: Mapped[PricingProvider] = mapped_column(
        Enum(PricingProvider), nullable=False, default=PricingProvider.aws
    )
    
    # Time range for this snapshot
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Cost breakdown (in USD)
    cpu_cost: Mapped[float] = mapped_column(DECIMAL(10, 4), nullable=False, default=0.0)
    memory_cost: Mapped[float] = mapped_column(DECIMAL(10, 4), nullable=False, default=0.0)
    storage_cost: Mapped[float] = mapped_column(DECIMAL(10, 4), nullable=False, default=0.0)
    total_cost: Mapped[float] = mapped_column(DECIMAL(10, 4), nullable=False, default=0.0)
    
    # Store detailed usage data as JSON
    usage_data_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PricingModel(Base):
    """Store cloud provider pricing configurations"""
    __tablename__ = "pricing_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_name: Mapped[PricingProvider] = mapped_column(
        Enum(PricingProvider), nullable=False, unique=True
    )
    
    # Pricing rates (per hour for CPU/Memory, per month for Storage)
    cpu_per_hour: Mapped[float] = mapped_column(DECIMAL(10, 6), nullable=False)  # $ per vCPU per hour
    memory_per_gb_hour: Mapped[float] = mapped_column(DECIMAL(10, 6), nullable=False)  # $ per GB per hour
    storage_per_gb_month: Mapped[float] = mapped_column(DECIMAL(10, 6), nullable=False)  # $ per GB per month
    
    # Optional: Different storage types
    storage_ssd_per_gb_month: Mapped[float] = mapped_column(DECIMAL(10, 6), nullable=True)
    storage_hdd_per_gb_month: Mapped[float] = mapped_column(DECIMAL(10, 6), nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
