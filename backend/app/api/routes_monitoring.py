"""
Monitoring API Routes
Provides endpoints for container metrics and real-time monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.container import Container, ContainerStatus
from app.services.container_stats_service import container_stats_service
from app.services.prometheus_metrics_service import prometheus_metrics_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class ContainerStatsResponse(BaseModel):
    """Container statistics response model"""
    id: int
    name: str
    container_id: Optional[str]
    status: str
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    memory_percent: float
    network_rx_bytes: int
    network_tx_bytes: int
    network_rx_mb: float
    network_tx_mb: float
    timestamp: str
    
    class Config:
        from_attributes = True


class MonitoringOverviewResponse(BaseModel):
    """Monitoring overview response"""
    total_containers: int
    running_containers: int
    stopped_containers: int
    total_cpu_percent: float
    total_memory_usage_mb: float
    containers_stats: List[ContainerStatsResponse]


@router.get("/containers", response_model=List[ContainerStatsResponse])
def get_all_containers_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time stats for all user's containers.
    """
    try:
        # Get user's containers
        containers = db.query(Container).filter(
            Container.user_id == current_user.id
        ).all()
        
        stats_list = []
        
        for container in containers:
            # Only get stats for running containers
            if container.status.value == 'running' and container.container_id:
                docker_stats = container_stats_service.get_container_stats(container.container_id)
                
                if docker_stats:
                    stats_list.append(ContainerStatsResponse(
                        id=container.id,
                        name=container.name,
                        container_id=container.container_id,
                        status=container.status.value,
                        cpu_percent=docker_stats['cpu_percent'],
                        memory_usage_mb=docker_stats['memory_usage_mb'],
                        memory_limit_mb=docker_stats['memory_limit_mb'],
                        memory_percent=docker_stats['memory_percent'],
                        network_rx_bytes=docker_stats['network_rx_bytes'],
                        network_tx_bytes=docker_stats['network_tx_bytes'],
                        network_rx_mb=docker_stats['network_rx_mb'],
                        network_tx_mb=docker_stats['network_tx_mb'],
                        timestamp=docker_stats['timestamp']
                    ))
                else:
                    # Container is running but stats unavailable
                    stats_list.append(ContainerStatsResponse(
                        id=container.id,
                        name=container.name,
                        container_id=container.container_id,
                        status=container.status.value,
                        cpu_percent=0.0,
                        memory_usage_mb=0.0,
                        memory_limit_mb=0.0,
                        memory_percent=0.0,
                        network_rx_bytes=0,
                        network_tx_bytes=0,
                        network_rx_mb=0.0,
                        network_tx_mb=0.0,
                        timestamp=""
                    ))
        
        return stats_list
        
    except Exception as e:
        logger.error(f"Error getting container stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get container stats: {str(e)}")


@router.get("/containers/{container_id}", response_model=ContainerStatsResponse)
def get_container_stats(
    container_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time stats for a specific container.
    """
    try:
        # Get container and verify ownership
        container = db.query(Container).filter(
            Container.id == container_id,
            Container.user_id == current_user.id
        ).first()
        
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")
        
        # Only get stats for running containers
        if container.status.value != 'running' or not container.container_id:
            return ContainerStatsResponse(
                id=container.id,
                name=container.name,
                container_id=container.container_id,
                status=container.status.value,
                cpu_percent=0.0,
                memory_usage_mb=0.0,
                memory_limit_mb=0.0,
                memory_percent=0.0,
                network_rx_bytes=0,
                network_tx_bytes=0,
                network_rx_mb=0.0,
                network_tx_mb=0.0,
                timestamp=""
            )
        
        docker_stats = container_stats_service.get_container_stats(container.container_id)
        
        if not docker_stats:
            raise HTTPException(status_code=500, detail="Failed to get container stats from Docker")
        
        return ContainerStatsResponse(
            id=container.id,
            name=container.name,
            container_id=container.container_id,
            status=container.status.value,
            cpu_percent=docker_stats['cpu_percent'],
            memory_usage_mb=docker_stats['memory_usage_mb'],
            memory_limit_mb=docker_stats['memory_limit_mb'],
            memory_percent=docker_stats['memory_percent'],
            network_rx_bytes=docker_stats['network_rx_bytes'],
            network_tx_bytes=docker_stats['network_tx_bytes'],
            network_rx_mb=docker_stats['network_rx_mb'],
            network_tx_mb=docker_stats['network_tx_mb'],
            timestamp=docker_stats['timestamp']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get container stats: {str(e)}")


@router.get("/overview", response_model=MonitoringOverviewResponse)
def get_monitoring_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get monitoring overview with aggregated stats.
    """
    try:
        logger.info(f"Monitoring overview requested by user {current_user.id} ({current_user.email})")
        
        # Get user's containers
        containers = db.query(Container).filter(
            Container.user_id == current_user.id
        ).all()
        
        logger.info(f"Found {len(containers)} total containers for user {current_user.id}")
        
        total_containers = len(containers)
        running_containers = sum(1 for c in containers if c.status.value == 'running')
        stopped_containers = total_containers - running_containers
        
        logger.info(f"Running: {running_containers}, Stopped: {stopped_containers}")
        
        stats_list = []
        total_cpu = 0.0
        total_memory = 0.0
        
        for container in containers:
            if container.status.value == 'running' and container.container_id:
                logger.info(f"Getting stats for container {container.id} ({container.name}) with Docker ID {container.container_id[:12]}")
                docker_stats = container_stats_service.get_container_stats(container.container_id)
                
                if docker_stats:
                    logger.info(f"Got stats for {container.name}: CPU={docker_stats['cpu_percent']}%, Mem={docker_stats['memory_usage_mb']}MB")
                    total_cpu += docker_stats['cpu_percent']
                    total_memory += docker_stats['memory_usage_mb']
                    
                    # Update Prometheus metrics
                    prometheus_metrics_service.update_container_metrics(
                        container_id=container.container_id,
                        container_name=container.name,
                        user_id=container.user_id
                    )
                    
                    stats_list.append(ContainerStatsResponse(
                        id=container.id,
                        name=container.name,
                        container_id=container.container_id,
                        status=container.status.value,
                        cpu_percent=docker_stats['cpu_percent'],
                        memory_usage_mb=docker_stats['memory_usage_mb'],
                        memory_limit_mb=docker_stats['memory_limit_mb'],
                        memory_percent=docker_stats['memory_percent'],
                        network_rx_bytes=docker_stats['network_rx_bytes'],
                        network_tx_bytes=docker_stats['network_tx_bytes'],
                        network_rx_mb=docker_stats['network_rx_mb'],
                        network_tx_mb=docker_stats['network_tx_mb'],
                        timestamp=docker_stats['timestamp']
                    ))
                else:
                    # Container marked as running but stats failed
                    # DON'T auto-stop - could be a simulated container
                    logger.warning(f"Failed to get Docker stats for {container.name} - container may be simulated")
        
        logger.info(f"Returning {len(stats_list)} container stats, Total CPU: {total_cpu}%, Total Memory: {total_memory}MB")
        
        return MonitoringOverviewResponse(
            total_containers=total_containers,
            running_containers=running_containers,
            stopped_containers=stopped_containers,
            total_cpu_percent=round(total_cpu, 2),
            total_memory_usage_mb=round(total_memory, 2),
            containers_stats=stats_list
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring overview: {str(e)}")


@router.get("/metrics")
def get_prometheus_metrics():
    """
    Get metrics in Prometheus format for scraping.
    This endpoint is called by Prometheus to collect metrics.
    """
    try:
        metrics_data = prometheus_metrics_service.get_metrics()
        return Response(content=metrics_data, media_type="text/plain; version=0.0.4")
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate metrics")
