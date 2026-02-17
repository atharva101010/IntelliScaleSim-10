import subprocess
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DockerService:
    """Docker service using CLI via subprocess for Windows compatibility."""
    
    def __init__(self):
        self.docker_command = 'docker'
    
    def _run_command(self, args: list, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a docker command via subprocess."""
        cmd = [self.docker_command] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker command failed: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            raise
        except FileNotFoundError:
            raise Exception("Docker CLI not found. Please ensure Docker Desktop is installed and in PATH.")
    
    def get_docker_status(self) -> dict:
        """Get detailed Docker status information."""
        status = {
            'available': False,
            'cli_installed': False,
            'engine_running': False,
            'version': None,
            'error': None,
            'message': None
        }
        
        try:
            # Test if Docker CLI is installed
            result = self._run_command(['version', '--format', '{{.Client.Version}}'], capture_output=True)
            status['cli_installed'] = True
            status['version'] = result.stdout.strip()
            
            # If we got here, Docker daemon is also running
            status['engine_running'] = True
            status['available'] = True
            status['message'] = f'Docker is available (version {status["version"]})'
            
        except subprocess.CalledProcessError as e:
            status['cli_installed'] = True
            error_msg = e.stderr.lower() if e.stderr else ''
            
            # Check for common Windows Docker Desktop errors
            if 'cannot connect' in error_msg or 'npipe' in error_msg or 'pipe' in error_msg:
                status['error'] = 'docker_desktop_not_running'
                status['message'] = 'Docker Desktop is not running. Please start Docker Desktop and try again.'
            elif 'daemon' in error_msg:
                status['error'] = 'docker_daemon_not_running'
                status['message'] = 'Docker daemon is not running. Please start Docker Desktop.'
            else:
                status['error'] = 'docker_connection_failed'
                status['message'] = f'Failed to connect to Docker: {e.stderr}'
            
            logger.warning(f"Docker engine not running: {e.stderr}")
            
        except FileNotFoundError:
            status['error'] = 'docker_not_installed'
            status['message'] = 'Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop'
            logger.warning("Docker CLI not found in PATH")
        
        except Exception as e:
            status['error'] = 'unknown_error'
            status['message'] = f'Unknown Docker error: {str(e)}'
            logger.error(f"Unexpected Docker error: {e}")
        
        return status
    
    @property
    def available(self) -> bool:
        """Check if Docker is available."""
        return self.get_docker_status()['available']
    
    def pull_image(self, image_name: str, username: Optional[str] = None, password: Optional[str] = None):
        """Pull a Docker image from Docker Hub."""
        # Login if credentials provided
        if username and password:
            try:
                login_result = subprocess.run(
                    [self.docker_command, 'login', '-u', username, '--password-stdin'],
                    input=password,
                    capture_output=True,
                    text=True,
                    check=True
                )
                logger.info(f"Docker login successful for user: {username}")
            except subprocess.CalledProcessError as e:
                raise Exception(f"Docker login failed: {e.stderr}")
        
        # Pull the image
        logger.info(f"Pulling image: {image_name}")
        try:
            self._run_command(['pull', image_name], capture_output=True)
            logger.info(f"Successfully pulled image: {image_name}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to pull image {image_name}: {e.stderr}")
    
    def list_local_images(self) -> list:
        """List all Docker images available locally."""
        try:
            result = self._run_command(['images', '--format', '{{.Repository}}:{{.Tag}}'], capture_output=True)
            images = result.stdout.strip().split('\n')
            # Filter out empty strings and <none>:<none> images
            return [img for img in images if img and img != '<none>:<none>']
        except Exception as e:
            logger.error(f"Failed to list Docker images: {e}")
            return []
    
    def image_exists_locally(self, image_name: str) -> bool:
        """Check if a Docker image exists locally."""
        try:
            result = self._run_command(['images', '-q', image_name], capture_output=True)
            exists = bool(result.stdout.strip())
            if exists:
                logger.info(f"Image '{image_name}' found locally")
            else:
                logger.info(f"Image '{image_name}' not found locally")
            return exists
        except Exception as e:
            logger.warning(f"Failed to check if image exists: {e}")
            return False
    
    def build_image_from_path(self, build_context: str, dockerfile_path: str, image_tag: str) -> str:
        """
        Build Docker image from a Dockerfile in a directory.
        
        Args:
            build_context: Path to build context directory
            dockerfile_path: Path to Dockerfile
            image_tag: Tag for the built image
            
        Returns:
            Image tag
            
        Raises:
            Exception: If build fails
        """
        try:
            logger.info(f"Building image '{image_tag}' from {dockerfile_path}")
            result = self._run_command([
                'build',
                '-t', image_tag,
                '-f', dockerfile_path,
                build_context
            ], capture_output=True)
            
            logger.info(f"Successfully built image: {image_tag}")
            return image_tag
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to build image: {e.stderr}")
            raise Exception(f"Failed to build image: {e.stderr}")
    
    def run_container(
        self,
        image: str,
        name: str,
        port: int,
        internal_port: int = 80,
        cpu_limit: str = "1.0",
        mem_limit: str = "512m",
        env_vars: dict = None,
        restart_policy: str = "always"
    ) -> str:
        """Run a Docker container and return its ID."""
        args = [
            'run',
            '-d',
            '--name', name,
            '-p', f'{port}:{internal_port}',
            '--cpus', cpu_limit,
            '--memory', mem_limit,
            '--restart', restart_policy,
        ]
        
        if env_vars:
            for key, value in env_vars.items():
                args.extend(['-e', f'{key}={value}'])
        
        args.append(image)
        
        try:
            result = self._run_command(args, capture_output=True)
            container_id = result.stdout.strip()
            logger.info(f"Container started: {name} (ID: {container_id[:12]})")
            return container_id
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to run container: {e.stderr}")
    
    def start_container(self, container_id: str):
        """Start a stopped container."""
        try:
            self._run_command(['start', container_id], capture_output=True)
            logger.info(f"Container started: {container_id[:12]}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to start container: {e.stderr}")
    
    def stop_container(self, container_id: str):
        """Stop a running container."""
        try:
            self._run_command(['stop', container_id], capture_output=True)
            logger.info(f"Container stopped: {container_id[:12]}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to stop container: {e.stderr}")
    
    def remove_container(self, container_id: str, force: bool = True):
        """Remove a container."""
        args = ['rm']
        if force:
            args.append('-f')
        args.append(container_id)
        
        try:
            self._run_command(args, capture_output=True)
            logger.info(f"Container removed: {container_id[:12]}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to remove container: {e.stderr}")
    
    def get_container_status(self, container_id: str) -> dict:
        """Get container status information."""
        try:
            result = self._run_command(['inspect', container_id], capture_output=True)
            data = json.loads(result.stdout)
            if data:
                container_info = data[0]
                return {
                    'id': container_info['Id'],
                    'status': container_info['State']['Status'],
                    'running': container_info['State']['Running'],
                    'name': container_info['Name'].lstrip('/'),
                }
            return {}
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to get container status: {e.stderr}")
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """Get container logs."""
        try:
            result = self._run_command(['logs', '--tail', str(tail), container_id], capture_output=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to get container logs: {e.stderr}")
    
    async def get_container_stats_async(self, container_id: str) -> dict:
        """
        Get container resource usage stats asynchronously.
        Returns CPU percentage and memory usage in MB.
        """
        import asyncio
        
        try:
            # Run Docker stats command (single sample, no streaming)
            proc = await asyncio.create_subprocess_exec(
                self.docker_command, 'stats', container_id, '--no-stream', '--format', '{{json .}}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.warning(f"Failed to get container stats: {stderr.decode()}")
                return {"cpu_percent": 0, "memory_usage_mb": 0}
            
            # Parse JSON output
            stats_json = json.loads(stdout.decode().strip())
            
            # Extract CPU (format: "X.XX%")
            cpu_str = stats_json.get('CPUPerc', '0%').rstrip('%')
            cpu_percent = float(cpu_str) if cpu_str else 0
            
            # Extract memory (format: "XXXMiB / YYYMiB" or "XXXGiB / YYYGiB")
            mem_str = stats_json.get('MemUsage', '0MiB / 0MiB').split(' / ')[0]
            if 'GiB' in mem_str:
                memory_mb = float(mem_str.rstrip('GiB')) * 1024
            elif 'MiB' in mem_str:
                memory_mb = float(mem_str.rstrip('MiB'))
            else:
                memory_mb = 0
            
            return {
                "cpu_percent": cpu_percent,
                "memory_usage_mb": memory_mb
            }
            
        except Exception as e:
            logger.warning(f"Failed to get container stats: {e}")
            return {"cpu_percent": 0, "memory_usage_mb": 0}

    def get_container_stats(self, container_id: str) -> dict:
        """
        Sync version of get_container_stats for non-async services.
        """
        try:
            # Use --no-stream. Capture output and clean it up.
            result = self._run_command(['stats', container_id, '--no-stream', '--format', '{{json .}}'], capture_output=True)
            output = result.stdout.strip()
            
            if not output:
                return {"cpu_percent": 0, "memory_mb": 0}

            # Docker stats sometimes includes escape codes or returns multiple lines
            # (header + data) even with --no-stream on some terminal environments.
            lines = [l.strip() for l in output.split('\n') if l.strip()]
            last_line = lines[-1]
            
            # Remove potential ANSI escape codes
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_line = ansi_escape.sub('', last_line)
            
            # Additional cleanup for garbage/repeated keys like "ID"ID" seen in some logs
            # We try to find the actual start and end of JSON { }
            start = clean_line.find('{')
            end = clean_line.rfind('}')
            if start != -1 and end != -1:
                clean_line = clean_line[start:end+1]
            
            stats_json = json.loads(clean_line)
            
            # Extract CPU. Key is 'CPUPerc'
            cpu_str = stats_json.get('CPUPerc', '0.00%').rstrip('%')
            cpu_percent = float(cpu_str) if cpu_str else 0.0
            
            # Extract memory. Key is 'MemUsage' (Format: "X.XMiB / Y.YGiB")
            mem_usage_str = stats_json.get('MemUsage', '0MiB / 0MiB').split(' / ')[0]
            
            # Parse memory string (MiB, GiB, B)
            memory_mb = 0.0
            if 'GiB' in mem_usage_str:
                memory_mb = float(mem_usage_str.replace('GiB', '')) * 1024.0
            elif 'MiB' in mem_usage_str:
                memory_mb = float(mem_usage_str.replace('MiB', ''))
            elif 'kB' in mem_usage_str:
                memory_mb = float(mem_usage_str.replace('kB', '')) / 1024.0
            elif 'B' in mem_usage_str:
                memory_mb = float(mem_usage_str.replace('B', '')) / (1024.0 * 1024.0)
                
            return {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb
            }
        except Exception as e:
            logger.warning(f"Failed to get sync container stats for {container_id}: {e}")
            return {"cpu_percent": 0, "memory_mb": 0}



_docker_service = None


def get_docker_service() -> DockerService:
    """Get the singleton Docker service instance."""
    global _docker_service
    if _docker_service is None:
        _docker_service = DockerService()
    return _docker_service
