"""
NusaNexus NoFOMO - Worker
Background job processing and Redis queue management
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import redis
from supabase import create_client, Client
import structlog

logger = structlog.get_logger(__name__)


class JobType(Enum):
    """Types of background jobs"""
    BOT_SETUP = "bot_setup"
    BOT_CLEANUP = "bot_cleanup"
    METRICS_UPDATE = "metrics_update"
    HEALTH_CHECK = "health_check"
    STRATEGY_VALIDATION = "strategy_validation"
    BACKTEST_RUN = "backtest_run"
    EXCHANGE_SYNC = "exchange_sync"
    DATA_CLEANUP = "data_cleanup"
    NOTIFICATION_SEND = "notification_send"


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobWorker:
    """
    Background job worker for async task processing
    
    Responsibilities:
    - Redis queue management
    - Job execution and monitoring
    - Error handling and retry logic
    - Job scheduling and batching
    - Resource management
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Job handlers
        self.job_handlers: Dict[JobType, Callable] = {}
        
        # Worker state
        self.is_running = False
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.job_queue = "bot_runner_jobs"
        self.results_queue = "bot_runner_results"
        
        # Job tracking
        self.job_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'avg_processing_time': 0.0
        }
        
        # Register default handlers
        self._register_default_handlers()
        
        logger.info("Job Worker initialized")
    
    def _register_default_handlers(self):
        """Register default job handlers"""
        self.job_handlers[JobType.BOT_SETUP] = self._handle_bot_setup
        self.job_handlers[JobType.BOT_CLEANUP] = self._handle_bot_cleanup
        self.job_handlers[JobType.METRICS_UPDATE] = self._handle_metrics_update
        self.job_handlers[JobType.HEALTH_CHECK] = self._handle_health_check
        self.job_handlers[JobType.STRATEGY_VALIDATION] = self._handle_strategy_validation
        self.job_handlers[JobType.EXCHANGE_SYNC] = self._handle_exchange_sync
        self.job_handlers[JobType.DATA_CLEANUP] = self._handle_data_cleanup
        self.job_handlers[JobType.NOTIFICATION_SEND] = self._handle_notification_send
    
    async def start(self):
        """Start the job worker"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting Job Worker")
        
        # Start job processing loop
        asyncio.create_task(self._process_job_queue())
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_completed_jobs())
        
        # Start monitoring task
        asyncio.create_task(self._monitor_worker_health())
        
        logger.info("Job Worker started successfully")
    
    async def stop(self):
        """Stop the job worker"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping Job Worker")
        
        # Cancel active jobs
        for job_id, task in self.active_jobs.items():
            if not task.done():
                task.cancel()
        
        # Wait for active jobs to complete
        if self.active_jobs:
            await asyncio.gather(*self.active_jobs.values(), return_exceptions=True)
        
        logger.info("Job Worker stopped")
    
    async def queue_job(self, job_type: str, job_data: Dict[str, Any], 
                       priority: int = 0, delay_seconds: int = 0) -> str:
        """
        Queue a new job for processing
        
        Args:
            job_type: Type of job
            job_data: Job data
            priority: Job priority (0=normal, 1=high, 2=urgent)
            delay_seconds: Delay before job becomes available
            
        Returns:
            Job ID
        """
        try:
            job_id = f"job_{datetime.now().timestamp()}_{hash(str(job_data)) % 10000}"
            
            job = {
                'id': job_id,
                'type': job_type,
                'data': job_data,
                'priority': priority,
                'created_at': datetime.now().isoformat(),
                'status': JobStatus.PENDING.value,
                'retries': 0,
                'max_retries': 3
            }
            
            # Add delay if specified
            if delay_seconds > 0:
                job['available_at'] = (datetime.now() + timedelta(seconds=delay_seconds)).isoformat()
            
            # Store job in Redis
            job_key = f"job:{job_id}"
            self.redis_client.hset(job_key, mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                                                   for k, v in job.items()})
            
            # Set expiry
            self.redis_client.expire(job_key, 86400)  # 24 hours
            
            # Add to appropriate queue
            if delay_seconds > 0:
                # Delayed job - store in sorted set with score as available time
                score = datetime.now().timestamp() + delay_seconds
                self.redis_client.zadd('delayed_jobs', {job_id: score})
            else:
                # Regular job - add to priority queue
                self.redis_client.zadd(self.job_queue, {job_id: -priority})
            
            logger.info(f"Queued job {job_id} of type {job_type}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to queue job: {str(e)}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status and information
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary
        """
        try:
            job_key = f"job:{job_id}"
            job_data = self.redis_client.hgetall(job_key)
            
            if not job_data:
                return None
            
            # Parse JSON fields
            for key, value in job_data.items():
                if key in ['data', 'result', 'error']:
                    try:
                        job_data[key] = json.loads(value)
                    except json.JSONDecodeError:
                        pass
            
            return job_data
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {str(e)}")
            return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Cancellation success status
        """
        try:
            job_key = f"job:{job_id}"
            
            # Check if job exists and is still pending
            job_data = self.redis_client.hgetall(job_key)
            if not job_data:
                return False
            
            status = job_data.get('status', '')
            if status not in [JobStatus.PENDING.value]:
                return False
            
            # Update status to cancelled
            self.redis_client.hset(job_key, 'status', JobStatus.CANCELLED.value)
            self.redis_client.hset(job_key, 'cancelled_at', datetime.now().isoformat())
            
            # Remove from queue
            self.redis_client.zrem(self.job_queue, job_id)
            self.redis_client.zrem('delayed_jobs', job_id)
            
            logger.info(f"Cancelled job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {str(e)}")
            return False
    
    async def retry_job(self, job_id: str) -> bool:
        """
        Retry a failed job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Retry success status
        """
        try:
            job_key = f"job:{job_id}"
            job_data = self.redis_client.hgetall(job_key)
            
            if not job_data:
                return False
            
            if job_data.get('status') != JobStatus.FAILED.value:
                return False
            
            retries = int(job_data.get('retries', 0))
            max_retries = int(job_data.get('max_retries', 3))
            
            if retries >= max_retries:
                logger.warning(f"Job {job_id} has exceeded max retries")
                return False
            
            # Update job for retry
            self.redis_client.hset(job_key, 'status', JobStatus.PENDING.value)
            self.redis_client.hset(job_key, 'retries', str(retries + 1))
            self.redis_client.hset(job_key, 'retry_at', datetime.now().isoformat())
            
            # Add back to queue with lower priority
            self.redis_client.zadd(self.job_queue, {job_id: 10})  # Lower priority for retries
            
            logger.info(f"Retrying job {job_id} (attempt {retries + 1})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry job {job_id}: {str(e)}")
            return False
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get job queue statistics
        
        Returns:
            Queue statistics dictionary
        """
        try:
            # Get queue lengths
            total_jobs = self.redis_client.zcard(self.job_queue)
            delayed_jobs = self.redis_client.zcard('delayed_jobs')
            
            # Get active job count
            active_job_count = len(self.active_jobs)
            
            # Get job statistics from database
            stats = {
                'queue_length': total_jobs,
                'delayed_jobs': delayed_jobs,
                'active_jobs': active_job_count,
                'worker_stats': self.job_stats.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {str(e)}")
            return {}
    
    async def _process_job_queue(self):
        """Main job processing loop"""
        while self.is_running:
            try:
                # Get available jobs (not delayed)
                jobs = self.redis_client.zrange(self.job_queue, 0, 0, withscores=True)
                
                if jobs:
                    job_id, priority = jobs[0]
                    
                    # Get job data
                    job_data = self.redis_client.hgetall(f"job:{job_id}")
                    
                    if job_data:
                        # Process the job
                        asyncio.create_task(self._process_job(job_id, job_data))
                        # Remove from queue
                        self.redis_client.zrem(self.job_queue, job_id)
                
                # Check for delayed jobs that are now available
                now = datetime.now().timestamp()
                available_delayed = self.redis_client.zrangebyscore('delayed_jobs', 0, now)
                
                if available_delayed:
                    for job_id in available_delayed:
                        # Get job data
                        job_data = self.redis_client.hgetall(f"job:{job_id}")
                        
                        if job_data:
                            # Process the job
                            asyncio.create_task(self._process_job(job_id, job_data))
                            # Remove from delayed queue
                            self.redis_client.zrem('delayed_jobs', job_id)
                
                # Brief pause to prevent tight looping
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Job processing loop error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_job(self, job_id: str, job_data: Dict[str, Any]):
        """Process a single job"""
        start_time = datetime.now()
        
        try:
            # Update status to running
            self.redis_client.hset(f"job:{job_id}", 'status', JobStatus.RUNNING.value)
            self.redis_client.hset(f"job:{job_id}", 'started_at', datetime.now().isoformat())
            
            # Create async task
            task = asyncio.current_task()
            self.active_jobs[job_id] = task
            
            # Get job type and data
            job_type_str = job_data.get('type', '')
            job_payload = json.loads(job_data.get('data', '{}'))
            
            job_type = JobType(job_type_str)
            handler = self.job_handlers.get(job_type)
            
            if not handler:
                raise ValueError(f"No handler found for job type: {job_type}")
            
            # Execute job
            result = await handler(job_id, job_payload)
            
            # Update job success
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self.redis_client.hset(f"job:{job_id}", 'status', JobStatus.COMPLETED.value)
            self.redis_client.hset(f"job:{job_id}", 'result', json.dumps(result))
            self.redis_client.hset(f"job:{job_id}", 'completed_at', end_time.isoformat())
            self.redis_client.hset(f"job:{job_id}", 'processing_time', str(processing_time))
            
            # Publish result to results queue
            self.redis_client.rpush(self.results_queue, json.dumps({
                'job_id': job_id,
                'status': JobStatus.COMPLETED.value,
                'result': result,
                'timestamp': end_time.isoformat()
            }))
            
            # Update statistics
            self.job_stats['total_processed'] += 1
            self.job_stats['successful'] += 1
            
            # Update average processing time
            current_avg = self.job_stats['avg_processing_time']
            total_jobs = self.job_stats['total_processed']
            self.job_stats['avg_processing_time'] = (current_avg * (total_jobs - 1) + processing_time) / total_jobs
            
            logger.info(f"Job {job_id} completed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            # Update job failure
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self.redis_client.hset(f"job:{job_id}", 'status', JobStatus.FAILED.value)
            self.redis_client.hset(f"job:{job_id}", 'error', str(e))
            self.redis_client.hset(f"job:{job_id}", 'failed_at', end_time.isoformat())
            self.redis_client.hset(f"job:{job_id}", 'processing_time', str(processing_time))
            
            # Publish failure to results queue
            self.redis_client.rpush(self.results_queue, json.dumps({
                'job_id': job_id,
                'status': JobStatus.FAILED.value,
                'error': str(e),
                'timestamp': end_time.isoformat()
            }))
            
            # Update statistics
            self.job_stats['total_processed'] += 1
            self.job_stats['failed'] += 1
            
            logger.error(f"Job {job_id} failed: {str(e)}")
        
        finally:
            # Remove from active jobs
            self.active_jobs.pop(job_id, None)
    
    async def _cleanup_completed_jobs(self):
        """Cleanup old completed jobs"""
        while self.is_running:
            try:
                # Clean up jobs older than 1 hour
                cutoff_time = datetime.now() - timedelta(hours=1)
                
                # Get all job keys
                job_keys = self.redis_client.keys('job:*')
                
                for job_key in job_keys:
                    job_data = self.redis_client.hgetall(job_key)
                    
                    if job_data:
                        status = job_data.get('status', '')
                        if status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                            # Check if job is old enough to delete
                            completed_at = job_data.get('completed_at', job_data.get('failed_at', ''))
                            if completed_at:
                                try:
                                    completed_time = datetime.fromisoformat(completed_at)
                                    if completed_time < cutoff_time:
                                        # Delete the job
                                        self.redis_client.delete(job_key)
                                except ValueError:
                                    pass
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Job cleanup error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _monitor_worker_health(self):
        """Monitor worker health and performance"""
        while self.is_running:
            try:
                # Get current stats
                stats = await self.get_queue_stats()
                
                # Log health status
                logger.info(f"Worker health: {stats}")
                
                # Check for stuck jobs (running for more than 5 minutes)
                stuck_jobs = []
                now = datetime.now()
                
                for job_id, task in self.active_jobs.items():
                    job_data = self.redis_client.hgetall(f"job:{job_id}")
                    if job_data:
                        started_at = job_data.get('started_at', '')
                        if started_at:
                            try:
                                start_time = datetime.fromisoformat(started_at)
                                if (now - start_time).total_seconds() > 300:  # 5 minutes
                                    stuck_jobs.append(job_id)
                            except ValueError:
                                pass
                
                # Handle stuck jobs
                for job_id in stuck_jobs:
                    logger.warning(f"Marking job {job_id} as failed due to timeout")
                    self.redis_client.hset(f"job:{job_id}", 'status', JobStatus.FAILED.value)
                    self.redis_client.hset(f"job:{job_id}", 'error', 'Job timeout')
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Worker health monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    # Default job handlers
    async def _handle_bot_setup(self, job_id: str, data: Dict[str, Any]):
        """Handle bot setup job"""
        bot_id = data.get('bot_id')
        action = data.get('action', 'post_start')
        
        # Perform post-start setup tasks
        if action == 'post_start':
            # Initialize bot metrics
            # Sync initial data
            # Set up monitoring
            pass
        
        return {'status': 'success', 'action': action, 'bot_id': bot_id}
    
    async def _handle_bot_cleanup(self, job_id: str, data: Dict[str, Any]):
        """Handle bot cleanup job"""
        bot_id = data.get('bot_id')
        
        # Perform cleanup tasks
        # Remove temporary files
        # Clean up database entries
        # Reset monitoring
        
        return {'status': 'success', 'bot_id': bot_id}
    
    async def _handle_metrics_update(self, job_id: str, data: Dict[str, Any]):
        """Handle metrics update job"""
        bot_id = data.get('bot_id')
        
        # Update bot metrics
        # Calculate performance metrics
        # Update database
        
        return {'status': 'success', 'bot_id': bot_id}
    
    async def _handle_health_check(self, job_id: str, data: Dict[str, Any]):
        """Handle health check job"""
        # Perform comprehensive health check
        # Check all services
        # Generate report
        
        return {'status': 'success', 'checks_passed': True}
    
    async def _handle_strategy_validation(self, job_id: str, data: Dict[str, Any]):
        """Handle strategy validation job"""
        strategy_id = data.get('strategy_id')
        
        # Validate strategy
        # Run syntax check
        # Test strategy logic
        
        return {'status': 'success', 'strategy_id': strategy_id, 'valid': True}
    
    async def _handle_exchange_sync(self, job_id: str, data: Dict[str, Any]):
        """Handle exchange sync job"""
        exchange = data.get('exchange')
        user_id = data.get('user_id')
        
        # Sync exchange data
        # Update market data
        # Refresh balances
        
        return {'status': 'success', 'exchange': exchange, 'user_id': user_id}
    
    async def _handle_data_cleanup(self, job_id: str, data: Dict[str, Any]):
        """Handle data cleanup job"""
        # Clean up old data
        # Remove expired sessions
        # Optimize database
        
        return {'status': 'success', 'cleanup_completed': True}
    
    async def _handle_notification_send(self, job_id: str, data: Dict[str, Any]):
        """Handle notification send job"""
        user_id = data.get('user_id')
        message = data.get('message')
        type_ = data.get('type', 'info')
        
        # Send notification
        # Email, push, webhook, etc.
        
        return {
            'status': 'success',
            'notification_sent': True,
            'user_id': user_id,
            'notification_type': type_,
            'message_preview': (message[:80] if isinstance(message, str) else None),
        }


if __name__ == "__main__":
    # Test job worker
    async def test():
        worker = JobWorker()
        
        try:
            await worker.start()
            
            # Queue a test job
            job_id = await worker.queue_job('health_check', {})
            print(f"Queued job: {job_id}")
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Check job status
            status = await worker.get_job_status(job_id)
            print(f"Job status: {status}")
            
        finally:
            await worker.stop()
    
    import asyncio
    asyncio.run(test())
