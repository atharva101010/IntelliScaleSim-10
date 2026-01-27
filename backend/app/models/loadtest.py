"""
Database models for Load Testing feature
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import Base


class LoadTestStatus(str, enum.Enum):
    """Load test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LoadTest(Base):
    """
    Load test configuration and results
    Stores the test parameters and aggregated results after completion
    """
    __tablename__ = "load_tests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    container_id = Column(Integer, ForeignKey("containers.id"), nullable=False, index=True)
    
    # Test configuration
    target_url = Column(String, nullable=False)
    total_requests = Column(Integer, nullable=False)  # 1-1000
    concurrency = Column(Integer, nullable=False)  # 1-50
    duration_seconds = Column(Integer, nullable=False)  # 10-60
    
    # Status
    status = Column(SQLEnum(LoadTestStatus), default=LoadTestStatus.PENDING, nullable=False, index=True)
    error_message = Column(String, nullable=True)
    
    # Results (populated during/after test)
    requests_sent = Column(Integer, default=0)
    requests_completed = Column(Integer, default=0)
    requests_failed = Column(Integer, default=0)
    
    # Response time statistics (in milliseconds)
    avg_response_time_ms = Column(Float, nullable=True)
    min_response_time_ms = Column(Float, nullable=True)
    max_response_time_ms = Column(Float, nullable=True)
    
    # Resource usage peaks
    peak_cpu_percent = Column(Float, nullable=True)
    peak_memory_mb = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="load_tests")
    container = relationship("Container", back_populates="load_tests")
    metrics = relationship("LoadTestMetric", back_populates="load_test", cascade="all, delete-orphan")


class LoadTestMetric(Base):
    """
    Time-series metrics collected during load test execution
    Captured every 2 seconds during the test for real-time monitoring
    """
    __tablename__ = "load_test_metrics"

    id = Column(Integer, primary_key=True, index=True)
    load_test_id = Column(Integer, ForeignKey("load_tests.id"), nullable=False, index=True)
    
    # Timestamp of this metric snapshot
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Container resource metrics
    cpu_percent = Column(Float, nullable=False)
    memory_mb = Column(Float, nullable=False)
    
    # Request progress at this timestamp
    requests_completed = Column(Integer, default=0)  # Cumulative
    requests_failed = Column(Integer, default=0)  # Cumulative
    active_requests = Column(Integer, default=0)  # Concurrent at this moment
    
    # Relationship
    load_test = relationship("LoadTest", back_populates="metrics")
