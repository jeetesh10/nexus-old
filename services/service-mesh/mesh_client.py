#!/usr/bin/env python3
"""
Service Mesh Client for Nexus Platform
Handles internal service-to-service communication with resilience patterns
"""
import json
import logging
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import yaml
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceConfig:
    host: str
    port: int
    health_check: str
    timeout: float
    retries: int
    failure_threshold: int
    recovery_timeout: float

class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_timeout: float):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class ServiceMeshClient:
    def __init__(self, config_path: str = None):
        self.services: Dict[str, ServiceConfig] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.load_config(config_path)
    
    def load_config(self, config_path: str = None):
        """Load service mesh configuration"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            # Default configuration
            config = {
                'services': {
                    'auth-api': {
                        'host': 'localhost',
                        'port': 8084,
                        'health_check': '/api/auth/health',
                        'timeout': 3.0,
                        'retries': 3,
                        'circuit_breaker': {
                            'failure_threshold': 5,
                            'recovery_timeout': 30.0
                        }
                    },
                    'access-control': {
                        'host': 'localhost',
                        'port': 8083,
                        'health_check': '/api/health',
                        'timeout': 3.0,
                        'retries': 3,
                        'circuit_breaker': {
                            'failure_threshold': 5,
                            'recovery_timeout': 30.0
                        }
                    },
                    'admin-dashboard': {
                        'host': 'localhost',
                        'port': 8081,
                        'health_check': '/health',
                        'timeout': 5.0,
                        'retries': 2,
                        'circuit_breaker': {
                            'failure_threshold': 3,
                            'recovery_timeout': 60.0
                        }
                    }
                }
            }
        
        # Initialize services
        for service_name, service_config in config['services'].items():
            self.services[service_name] = ServiceConfig(
                host=service_config['host'],
                port=service_config['port'],
                health_check=service_config['health_check'],
                timeout=service_config['timeout'],
                retries=service_config['retries'],
                failure_threshold=service_config['circuit_breaker']['failure_threshold'],
                recovery_timeout=service_config['circuit_breaker']['recovery_timeout']
            )
            
            # Initialize circuit breaker
            self.circuit_breakers[service_name] = CircuitBreaker(
                failure_threshold=service_config['circuit_breaker']['failure_threshold'],
                recovery_timeout=service_config['circuit_breaker']['recovery_timeout']
            )
    
    async def start(self):
        """Start the service mesh client"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
        )
        logger.info("Service mesh client started")
    
    async def stop(self):
        """Stop the service mesh client"""
        if self.session:
            await self.session.close()
        logger.info("Service mesh client stopped")
    
    async def check_service_health(self, service_name: str) -> ServiceStatus:
        """Check if a service is healthy"""
        if service_name not in self.services:
            return ServiceStatus.UNKNOWN
        
        service = self.services[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        
        if not circuit_breaker.can_execute():
            return ServiceStatus.UNHEALTHY
        
        try:
            health_url = f"http://{service.host}:{service.port}{service.health_check}"
            async with self.session.get(health_url, timeout=service.timeout) as response:
                if response.status == 200:
                    circuit_breaker.on_success()
                    return ServiceStatus.HEALTHY
                else:
                    circuit_breaker.on_failure()
                    return ServiceStatus.UNHEALTHY
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            circuit_breaker.on_failure()
            return ServiceStatus.UNHEALTHY
    
    async def call_service(self, service_name: str, method: str, path: str, 
                          data: Dict = None, headers: Dict = None) -> Optional[Dict]:
        """Call a service with resilience patterns"""
        if service_name not in self.services:
            logger.error(f"Service {service_name} not found")
            return None
        
        service = self.services[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker open for {service_name}")
            return None
        
        # Prepare request
        url = f"http://{service.host}:{service.port}{path}"
        request_headers = headers or {}
        
        # Retry logic
        for attempt in range(service.retries):
            try:
                if method.upper() == 'GET':
                    async with self.session.get(url, headers=request_headers, 
                                               timeout=service.timeout) as response:
                        if response.status == 200:
                            circuit_breaker.on_success()
                            return await response.json()
                        else:
                            circuit_breaker.on_failure()
                            logger.error(f"Service {service_name} returned {response.status}")
                            return None
                
                elif method.upper() == 'POST':
                    async with self.session.post(url, json=data, headers=request_headers,
                                                timeout=service.timeout) as response:
                        if response.status == 200:
                            circuit_breaker.on_success()
                            return await response.json()
                        else:
                            circuit_breaker.on_failure()
                            logger.error(f"Service {service_name} returned {response.status}")
                            return None
                
                else:
                    logger.error(f"Unsupported method: {method}")
                    return None
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {service_name} (attempt {attempt + 1})")
                circuit_breaker.on_failure()
                if attempt == service.retries - 1:
                    return None
                await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Error calling {service_name}: {e}")
                circuit_breaker.on_failure()
                if attempt == service.retries - 1:
                    return None
                await asyncio.sleep(0.1 * (2 ** attempt))
        
        return None
    
    async def get_service_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services"""
        status = {}
        tasks = []
        
        for service_name in self.services:
            task = asyncio.create_task(self.check_service_health(service_name))
            tasks.append((service_name, task))
        
        for service_name, task in tasks:
            status[service_name] = await task
        
        return status
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict]:
        """Get circuit breaker status for all services"""
        status = {}
        for service_name, cb in self.circuit_breakers.items():
            status[service_name] = {
                'state': cb.state,
                'failure_count': cb.failure_count,
                'last_failure_time': cb.last_failure_time
            }
        return status

# Example usage
class ServiceExample:
    def __init__(self):
        self.mesh_client = ServiceMeshClient()
    
    async def validate_token(self, token: str) -> Optional[Dict]:
        """Validate token using auth-api service"""
        return await self.mesh_client.call_service(
            service_name='auth-api',
            method='GET',
            path=f'/api/auth/validate-token?token={token}'
        )
    
    async def get_user_services(self, groups: List[str]) -> Optional[Dict]:
        """Get user services using access-control service"""
        groups_param = ','.join(groups)
        return await self.mesh_client.call_service(
            service_name='access-control',
            method='GET',
            path=f'/api/user-access?groups={groups_param}'
        )
    
    async def get_admin_dashboard_data(self) -> Optional[Dict]:
        """Get admin dashboard data"""
        return await self.mesh_client.call_service(
            service_name='admin-dashboard',
            method='GET',
            path='/api/dashboard'
        )

# Async context manager
class ServiceMeshContext:
    def __init__(self, config_path: str = None):
        self.mesh_client = ServiceMeshClient(config_path)
    
    async def __aenter__(self):
        await self.mesh_client.start()
        return self.mesh_client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mesh_client.stop()

# Example usage
async def main():
    """Example usage of service mesh client"""
    async with ServiceMeshContext() as mesh_client:
        # Check service health
        status = await mesh_client.get_service_status()
        print("Service Status:", status)
        
        # Get circuit breaker status
        cb_status = mesh_client.get_circuit_breaker_status()
        print("Circuit Breaker Status:", cb_status)
        
        # Example service call
        example = ServiceExample()
        result = await example.validate_token("test-token")
        print("Token validation result:", result)

if __name__ == "__main__":
    asyncio.run(main())
