from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class ScalingPolicy(Base):
    """
    Auto-scaling policy configuration for a container
    Defines when and how to scale based on resource metrics
    """
    __tablename__ = "scaling_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(Integer, ForeignKey("containers.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Scale Up Configuration
    scale_up_cpu_threshold = Column(Float, default=80.0, nullable=False)
    scale_up_memory_threshold = Column(Float, default=80.0, nullable=False)
    min_replicas = Column(Integer, default=1, nullable=False)
    max_replicas = Column(Integer, default=8, nullable=False)
    
    # Scale Down Configuration
    scale_down_cpu_threshold = Column(Float, default=30.0, nullable=False)
    scale_down_memory_threshold = Column(Float, default=30.0, nullable=False)
    
    # Load Balancing
    load_balancer_enabled = Column(Boolean, default=True, nullable=False)
    load_balancer_port = Column(Integer, nullable=True)
    
    # Timing
    cooldown_period = Column(Integer, default=300, nullable=False)  # 5 minutes
    evaluation_period = Column(Integer, default=60, nullable=False)  # 1 minute
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    last_scaled_at = Column(DateTime(timezone=True), nullable=True)


class ScalingEvent(Base):
    """
    Record of scaling actions taken
    Provides audit trail and history
    """
    __tablename__ = "scaling_events"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("scaling_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    container_id = Column(Integer, ForeignKey("containers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action = Column(String(20), nullable=False)  # 'scale_up' or 'scale_down'
    trigger_metric = Column(String(20), nullable=False)  # 'cpu' or 'memory'
    metric_value = Column(Float, nullable=False)
    
    replica_count_before = Column(Integer, nullable=False)
    replica_count_after = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
