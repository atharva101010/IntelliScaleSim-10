"""
Container Stats Service
Collects real-time metrics from Docker containers including CPU, memory, and network usage.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
import subprocess
import json
import asyncio

logger = logging.getLogger(__name__)


class ContainerStatsService:
    """Service for collecting Docker container statistics"""
    
    def __init__(self):
        self.use_cli = True  # Use CLI mode for Windows compatibility
        logger.info("Container stats service initialized (CLI mode)")
    
    async def get_container_stats(self, container_id: str) -> Optional[Dict]:
        """
        Get real-time stats for a specific container using docker CLI.
        """
        try:
            # Use docker stats command with JSON format
            cmd = [
                'docker', 'stats', container_id,
                '--no-stream', '--format',
                '{"cpu":"{{.CPUPerc}}","mem":"{{.MemUsage}}","net":"{{.NetIO}}"}'
            ]
            
            # Run in a thread to avoid blocking the event loop
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, timeout=5
            )
            
            if result.returncode != 0:
                logger.warning(f"Docker stats command failed for {container_id}: {result.stderr}")
                return None
            
            # Parse the output
            stats_json = json.loads(result.stdout.strip())
            
            # Parse CPU (e.g., "0.05%" -> 0.05)
            cpu_str = stats_json['cpu'].replace('%', '')
            cpu_percent = float(cpu_str) if cpu_str else 0.0
            
            # Parse memory (e.g., "45.09MiB / 512MiB" -> usage and limit)
            mem_str = stats_json['mem']
            mem_parts = mem_str.split(' / ')
            memory_usage_mb = self._parse_memory(mem_parts[0]) if len(mem_parts) > 0 else 0.0
            memory_limit_mb = self._parse_memory(mem_parts[1]) if len(mem_parts) > 1 else 0.0
            memory_percent = (memory_usage_mb / memory_limit_mb * 100) if memory_limit_mb > 0 else 0.0
            
            # Parse network (e.g., "1.2MB / 500kB" -> rx and tx)
            net_str = stats_json['net']
            net_parts = net_str.split(' / ')
            network_rx_mb = self._parse_network(net_parts[0]) if len(net_parts) > 0 else 0.0
            network_tx_mb = self._parse_network(net_parts[1]) if len(net_parts) > 1 else 0.0
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage_mb, 2),
                'memory_limit_mb': round(memory_limit_mb, 2),
                'memory_percent': round(memory_percent, 2),
                'network_rx_bytes': int(network_rx_mb * 1024 * 1024),
                'network_tx_bytes': int(network_tx_mb * 1024 * 1024),
                'network_rx_mb': round(network_rx_mb, 2),
                'network_tx_mb': round(network_tx_mb, 2),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting stats for {container_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting stats for {container_id}: {e}")
            return None
    
    def _parse_memory(self, mem_str: str) -> float:
        """Parse memory string like '45.09MiB' or '1.2GiB' to MB"""
        try:
            mem_str = mem_str.strip()
            if 'GiB' in mem_str or 'GB' in mem_str:
                value = float(mem_str.replace('GiB', '').replace('GB', ''))
                return value * 1024
            elif 'MiB' in mem_str or 'MB' in mem_str:
                return float(mem_str.replace('MiB', '').replace('MB', ''))
            elif 'KiB' in mem_str or 'KB' in mem_str:
                value = float(mem_str.replace('KiB', '').replace('KB', ''))
                return value / 1024
            else:
                return 0.0
        except:
            return 0.0
    
    def _parse_network(self, net_str: str) -> float:
        """Parse network string like '1.2MB' or '500kB' to MB"""
        try:
            net_str = net_str.strip()
            if 'GB' in net_str:
                value = float(net_str.replace('GB', ''))
                return value * 1024
            elif 'MB' in net_str:
                return float(net_str.replace('MB', ''))
            elif 'kB' in net_str or 'KB' in net_str:
                value = float(net_str.replace('kB', '').replace('KB', ''))
                return value / 1024
            elif 'B' in net_str:
                value = float(net_str.replace('B', ''))
                return value / (1024 * 1024)
            else:
                return 0.0
        except:
            return 0.0
    
    def get_all_containers_stats(self) -> List[Dict]:
        """
        Get stats for all running containers.
        
        Returns:
            List of stats dictionaries
        """
        # This method is not actively used, but kept for compatibility
        return []


# Singleton instance
container_stats_service = ContainerStatsService()
