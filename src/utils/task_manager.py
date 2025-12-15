#!/usr/bin/env python3
"""
Background task manager
Manages long-running generation tasks with progress tracking
"""

import asyncio
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class Task:
    """Represents a background task."""
    task_id: str
    name: str
    status: str  # pending, running, completed, failed
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None

class BackgroundTaskManager:
    """Manage background tasks with progress tracking."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_task(
        self,
        name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> str:
        """
        Create and start a background task.
        
        Args:
            name: Task name
            func: Async function to run
            *args, **kwargs: Function arguments
        
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]
        
        # Create task record
        task = Task(
            task_id=task_id,
            name=name,
            status="pending"
        )
        self.tasks[task_id] = task
        
        # Start async task
        async_task = asyncio.create_task(
            self._run_task(task_id, func, *args, **kwargs)
        )
        self._running_tasks[task_id] = async_task
        
        return task_id
    
    async def _run_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ):
        """Execute task with error handling."""
        task = self.tasks[task_id]
        
        try:
            task.status = "running"
            task.started_at = datetime.now()
            
            # Execute function
            result = await func(*args, **kwargs)
            
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result
            task.progress = 100.0
            
        except Exception as e:
            task.status = "failed"
            task.completed_at = datetime.now()
            task.error = str(e)
            print(f"Task {task_id} failed: {e}")
        
        finally:
            # Cleanup
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def update_progress(self, task_id: str, progress: float, status: str = None):
        """Update task progress."""
        if task_id in self.tasks:
            self.tasks[task_id].progress = min(100.0, max(0.0, progress))
            if status:
                self.tasks[task_id].status = status
    
    def list_tasks(self, limit: int = 10) -> list:
        """List recent tasks."""
        tasks = sorted(
            self.tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )
        return tasks[:limit]
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove old completed/failed tasks."""
        now = datetime.now()
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in ["completed", "failed"]:
                age = (now - task.created_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
        
        return len(to_remove)


# Global task manager
task_manager = BackgroundTaskManager()
