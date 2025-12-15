#!/usr/bin/env python3
"""
Health monitoring and system status
Track API health, resource usage, queue status
"""

import psutil
import time
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class HealthMonitor:
    """Monitor system health and resources."""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Uptime
        uptime_seconds = time.time() - self.start_time
        uptime_str = self._format_uptime(uptime_seconds)
        
        # Disk space for outputs
        output_dir = Path("outputs")
        output_size = sum(f.stat().st_size for f in output_dir.rglob('*') if f.is_file()) if output_dir.exists() else 0
        output_size_mb = output_size / (1024 * 1024)
        
        return {
            "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "degraded",
            "timestamp": datetime.now().isoformat(),
            "uptime": uptime_str,
            "uptime_seconds": int(uptime_seconds),
            "requests": {
                "total": self.request_count,
                "errors": self.error_count,
                "success_rate": self._calculate_success_rate()
            },
            "resources": {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_used_gb": round(memory.used / (1024 ** 3), 2),
                "memory_total_gb": round(memory.total / (1024 ** 3), 2),
                "disk_percent": round(disk.percent, 1),
                "disk_free_gb": round(disk.free / (1024 ** 3), 2)
            },
            "storage": {
                "output_size_mb": round(output_size_mb, 2),
                "output_files": sum(1 for _ in output_dir.rglob('*') if output_dir.exists() else 0)
            }
        }
    
    def increment_request(self):
        """Increment request counter."""
        self.request_count += 1
    
    def increment_error(self):
        """Increment error counter."""
        self.error_count += 1
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.request_count == 0:
            return 100.0
        return round(((self.request_count - self.error_count) / self.request_count) * 100, 2)
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime as human-readable string."""
        seconds = int(seconds)
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)


# Global health monitor instance
health_monitor = HealthMonitor()
