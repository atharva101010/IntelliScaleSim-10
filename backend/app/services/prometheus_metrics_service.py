"""
Prometheus Metrics Service
Exposes container metrics in Prometheus format for scraping.
"""

from prometheus_client import Gauge, Counter, CollectorRegistry, generate_latest
import logging
from typing import Dict
from app.services.container_stats_service import container_stats_service

logger = logging.getLogger(__name__)


class PrometheusMetricsService:
    """Service for exposing container metrics to Prometheus"""
    
    def __init__(self):
        # Create a custom registry
        self.registry = CollectorRegistry()
        
        # Define metrics with labels
        self.cpu_usage = Gauge(
            'container_cpu_usage_percent',
            'Container CPU usage percentage',
            ['container_id', 'container_name', 'user_id'],
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'container_memory_usage_bytes',
            'Container memory usage in bytes',
            ['container_id', 'container_name', 'user_id'],
            registry=self.registry
        )
        
        self.memory_limit = Gauge(
            'container_memory_limit_bytes',
            'Container memory limit in bytes',
            ['container_id', 'container_name', 'user_id'],
            registry=self.registry
        )
        
        self.network_rx_bytes = Gauge(
            'container_network_rx_bytes',
            'Container network bytes received',
            ['container_id', 'container_name', 'user_id'],
            registry=self.registry
        )
        
        self.network_tx_bytes = Gauge(
            'container_network_tx_bytes',
            'Container network bytes transmitted',
            ['container_id', 'container_name', 'user_id'],
            registry=self.registry
        )
        
        logger.info("Prometheus metrics service initialized")
    
    def update_container_metrics(self, container_id: str, container_name: str, user_id: int):
        """
        Update metrics for a specific container.
        
        Args:
            container_id: Docker container ID
            container_name: Container name
            user_id: User ID who owns the container
        """
        try:
            # Get stats from the stats service
            stats = container_stats_service.get_container_stats(container_id)
            
            if not stats:
                logger.warning(f"Could not get stats for container {container_name}")
                return
            
            labels = {
                'container_id': container_id[:12],  # Short ID
                'container_name': container_name,
                'user_id': str(user_id)
            }
            
            # Update metrics
            self.cpu_usage.labels(**labels).set(stats['cpu_percent'])
            self.memory_usage.labels(**labels).set(stats['memory_usage_mb'] * 1024 * 1024)  # Convert to bytes
            self.memory_limit.labels(**labels).set(stats['memory_limit_mb'] * 1024 * 1024)  # Convert to bytes
            self.network_rx_bytes.labels(**labels).set(stats['network_rx_bytes'])
            self.network_tx_bytes.labels(**labels).set(stats['network_tx_bytes'])
            
            logger.debug(f"Updated metrics for container {container_name}")
            
        except Exception as e:
            logger.error(f"Error updating metrics for container {container_name}: {e}")
    
    def get_metrics(self) -> bytes:
        """
        Get metrics in Prometheus text format.
        
        Returns:
            Metrics as bytes in Prometheus format
        """
        return generate_latest(self.registry)


# Singleton instance
prometheus_metrics_service = PrometheusMetricsService()
