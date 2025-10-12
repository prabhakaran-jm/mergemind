#!/usr/bin/env python3
"""
Async optimization utilities for MergeMind.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
import threading
from functools import wraps
import weakref

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AsyncTask:
    """Async task definition."""
    task_id: str
    coroutine: Awaitable[Any]
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None

class AsyncTaskManager:
    """Async task manager with priority queue and resource management."""
    
    def __init__(self, max_concurrent_tasks: int = 10, max_workers: int = 4):
        """Initialize async task manager."""
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_workers = max_workers
        
        # Task management
        self.task_queue = asyncio.PriorityQueue()
        self.running_tasks = {}
        self.completed_tasks = {}
        self.failed_tasks = {}
        
        # Thread pool for CPU-bound tasks
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'total_execution_time': 0.0,
            'avg_execution_time': 0.0
        }
        
        # Event loop
        self.loop = None
        self.manager_task = None
        self.running = False
        
        logger.info(f"Async task manager initialized: max_concurrent={max_concurrent_tasks}, max_workers={max_workers}")
    
    async def start(self):
        """Start the task manager."""
        if self.running:
            return
        
        self.running = True
        self.loop = asyncio.get_event_loop()
        self.manager_task = asyncio.create_task(self._task_manager_loop())
        logger.info("Async task manager started")
    
    async def stop(self):
        """Stop the task manager."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all pending tasks
        while not self.task_queue.empty():
            try:
                _, task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                task.status = TaskStatus.CANCELLED
            except asyncio.TimeoutError:
                break
        
        # Wait for running tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        # Cancel manager task
        if self.manager_task:
            self.manager_task.cancel()
            try:
                await self.manager_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        logger.info("Async task manager stopped")
    
    async def submit_task(self, 
                         coroutine: Awaitable[Any],
                         priority: TaskPriority = TaskPriority.NORMAL,
                         task_id: Optional[str] = None,
                         max_retries: int = 3,
                         timeout: Optional[float] = None) -> str:
        """Submit a task for execution."""
        if not task_id:
            task_id = f"task_{int(time.time() * 1000)}"
        
        task = AsyncTask(
            task_id=task_id,
            coroutine=coroutine,
            priority=priority,
            created_at=datetime.utcnow(),
            max_retries=max_retries,
            timeout=timeout
        )
        
        # Add to priority queue (lower priority number = higher priority)
        priority_value = 5 - priority.value  # Invert priority
        await self.task_queue.put((priority_value, task))
        
        self.stats['total_tasks'] += 1
        logger.debug(f"Task {task_id} submitted with priority {priority.name}")
        
        return task_id
    
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get task result."""
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].result
        elif task_id in self.failed_tasks:
            raise self.failed_tasks[task_id].error
        else:
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            # Note: We can't actually cancel a running coroutine, just mark it as cancelled
            return True
        return False
    
    async def _task_manager_loop(self):
        """Main task manager loop."""
        while self.running:
            try:
                # Wait for next task
                priority, task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Check if we can run more tasks
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    # Put task back and wait
                    await self.task_queue.put((priority, task))
                    await asyncio.sleep(0.1)
                    continue
                
                # Start task
                asyncio.create_task(self._execute_task(task))
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Task manager loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _execute_task(self, task: AsyncTask):
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        self.running_tasks[task.task_id] = task
        
        try:
            # Execute task with timeout if specified
            if task.timeout:
                result = await asyncio.wait_for(task.coroutine, timeout=task.timeout)
            else:
                result = await task.coroutine
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            
            # Update statistics
            execution_time = (task.completed_at - task.started_at).total_seconds()
            self.stats['completed_tasks'] += 1
            self.stats['total_execution_time'] += execution_time
            self.stats['avg_execution_time'] = (
                self.stats['total_execution_time'] / self.stats['completed_tasks']
            )
            
            # Move to completed tasks
            self.completed_tasks[task.task_id] = task
            
            logger.debug(f"Task {task.task_id} completed in {execution_time:.2f}s")
            
        except asyncio.TimeoutError:
            # Task timed out
            task.status = TaskStatus.FAILED
            task.error = asyncio.TimeoutError(f"Task {task.task_id} timed out")
            self.failed_tasks[task.task_id] = task
            self.stats['failed_tasks'] += 1
            
            logger.warning(f"Task {task.task_id} timed out")
            
        except Exception as e:
            # Task failed
            task.status = TaskStatus.FAILED
            task.error = e
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                
                # Re-submit task with lower priority
                priority_value = 5 - task.priority.value + task.retry_count
                await self.task_queue.put((priority_value, task))
                
                logger.info(f"Task {task.task_id} failed, retrying ({task.retry_count}/{task.max_retries})")
            else:
                self.failed_tasks[task.task_id] = task
                self.stats['failed_tasks'] += 1
                logger.error(f"Task {task.task_id} failed after {task.max_retries} retries: {e}")
        
        finally:
            # Remove from running tasks
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task manager statistics."""
        return {
            'total_tasks': self.stats['total_tasks'],
            'completed_tasks': self.stats['completed_tasks'],
            'failed_tasks': self.stats['failed_tasks'],
            'cancelled_tasks': self.stats['cancelled_tasks'],
            'running_tasks': len(self.running_tasks),
            'pending_tasks': self.task_queue.qsize(),
            'avg_execution_time': self.stats['avg_execution_time'],
            'total_execution_time': self.stats['total_execution_time'],
            'success_rate': (
                self.stats['completed_tasks'] / self.stats['total_tasks'] 
                if self.stats['total_tasks'] > 0 else 0
            )
        }
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status."""
        if task_id in self.running_tasks:
            return self.running_tasks[task_id].status
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id].status
        elif task_id in self.failed_tasks:
            return self.failed_tasks[task_id].status
        else:
            return None

class AsyncBatchProcessor:
    """Async batch processor for handling multiple operations efficiently."""
    
    def __init__(self, batch_size: int = 100, max_concurrent_batches: int = 5):
        """Initialize batch processor."""
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        logger.info(f"Async batch processor initialized: batch_size={batch_size}, max_concurrent={max_concurrent_batches}")
    
    async def process_batches(self, 
                            items: List[Any],
                            process_func: Callable[[List[Any]], Awaitable[Any]],
                            progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Any]:
        """Process items in batches."""
        results = []
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size
        
        # Create batches
        batches = [
            items[i:i + self.batch_size] 
            for i in range(0, len(items), self.batch_size)
        ]
        
        # Process batches concurrently
        async def process_single_batch(batch: List[Any], batch_index: int) -> Any:
            async with self.semaphore:
                try:
                    result = await process_func(batch)
                    if progress_callback:
                        progress_callback(batch_index + 1, total_batches)
                    return result
                except Exception as e:
                    logger.error(f"Batch {batch_index} failed: {e}")
                    raise
        
        # Execute all batches
        batch_tasks = [
            process_single_batch(batch, i) 
            for i, batch in enumerate(batches)
        ]
        
        results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        logger.info(f"Processed {len(batches)} batches, {len(valid_results)} successful")
        
        return valid_results

class AsyncRateLimiter:
    """Async rate limiter for controlling request rates."""
    
    def __init__(self, rate_limit: int, time_window: float = 1.0):
        """Initialize rate limiter."""
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests = []
        self.lock = asyncio.Lock()
        
        logger.info(f"Async rate limiter initialized: {rate_limit} requests per {time_window}s")
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request."""
        async with self.lock:
            now = time.time()
            
            # Remove old requests
            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
            
            # Check if we can make a request
            if len(self.requests) < self.rate_limit:
                self.requests.append(now)
                return True
            
            return False
    
    async def wait_for_slot(self) -> None:
        """Wait until a slot is available."""
        while not await self.acquire():
            await asyncio.sleep(0.1)

class AsyncConnectionPool:
    """Async connection pool for managing database connections."""
    
    def __init__(self, 
                 create_connection: Callable[[], Awaitable[Any]],
                 max_connections: int = 10,
                 min_connections: int = 2):
        """Initialize connection pool."""
        self.create_connection = create_connection
        self.max_connections = max_connections
        self.min_connections = min_connections
        
        self.connections = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = asyncio.Lock()
        
        logger.info(f"Async connection pool initialized: max={max_connections}, min={min_connections}")
    
    async def initialize(self):
        """Initialize the connection pool."""
        async with self.lock:
            for _ in range(self.min_connections):
                connection = await self.create_connection()
                await self.connections.put(connection)
                self.active_connections += 1
        
        logger.info(f"Connection pool initialized with {self.min_connections} connections")
    
    async def get_connection(self) -> Any:
        """Get a connection from the pool."""
        try:
            # Try to get existing connection
            connection = await asyncio.wait_for(self.connections.get(), timeout=1.0)
            return connection
        except asyncio.TimeoutError:
            # Create new connection if under limit
            async with self.lock:
                if self.active_connections < self.max_connections:
                    connection = await self.create_connection()
                    self.active_connections += 1
                    return connection
                else:
                    # Wait for a connection to become available
                    return await self.connections.get()
    
    async def return_connection(self, connection: Any):
        """Return a connection to the pool."""
        try:
            await self.connections.put(connection)
        except Exception as e:
            logger.error(f"Failed to return connection: {e}")
            async with self.lock:
                self.active_connections -= 1
    
    async def close_all(self):
        """Close all connections in the pool."""
        async with self.lock:
            while not self.connections.empty():
                try:
                    connection = await self.connections.get()
                    if hasattr(connection, 'close'):
                        await connection.close()
                except Exception as e:
                    logger.error(f"Failed to close connection: {e}")
            
            self.active_connections = 0
        
        logger.info("All connections closed")

# Global async manager instance
async_task_manager = AsyncTaskManager()

def async_task(priority: TaskPriority = TaskPriority.NORMAL, 
              max_retries: int = 3, 
              timeout: Optional[float] = None):
    """Decorator for async task execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            task_id = await async_task_manager.submit_task(
                func(*args, **kwargs),
                priority=priority,
                max_retries=max_retries,
                timeout=timeout
            )
            return await async_task_manager.get_task_result(task_id)
        return wrapper
    return decorator

def async_batch(batch_size: int = 100, max_concurrent: int = 5):
    """Decorator for async batch processing."""
    def decorator(func):
        @wraps(func)
        async def wrapper(items: List[Any], *args, **kwargs):
            processor = AsyncBatchProcessor(batch_size, max_concurrent)
            return await processor.process_batches(items, lambda batch: func(batch, *args, **kwargs))
        return wrapper
    return decorator

def rate_limited(rate_limit: int, time_window: float = 1.0):
    """Decorator for rate limiting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            limiter = AsyncRateLimiter(rate_limit, time_window)
            await limiter.wait_for_slot()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def start_async_manager():
    """Start the global async task manager."""
    await async_task_manager.start()

async def stop_async_manager():
    """Stop the global async task manager."""
    await async_task_manager.stop()

def get_async_stats() -> Dict[str, Any]:
    """Get async task manager statistics."""
    return async_task_manager.get_stats()
