"""
Scheduler implementation for QuickScrape.

This module provides a simple job scheduler that manages and runs
scraping jobs based on their schedules.
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Set, Union, Callable

from quickscrape.config import config_manager
from quickscrape.scraper import create_scraper, run_scraper
from quickscrape.scheduling.job_manager import JobManager
from quickscrape.scheduling.models import Job, JobStatus
from quickscrape.utils.logger import get_logger

logger = get_logger(__name__)


class Scheduler:
    """
    Simple scheduler for running scraping jobs.

    The scheduler periodically checks for pending jobs and
    executes them based on their schedules.
    """

    def __init__(self, job_manager: Optional[JobManager] = None) -> None:
        """
        Initialize the scheduler.

        Args:
            job_manager: Optional job manager (creates one if not provided)
        """
        self.job_manager = job_manager or JobManager()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.check_interval = 60  # Check for jobs every 60 seconds
        self.running_jobs: Set[str] = set()  # Set of currently running job IDs
        self.job_completed_callbacks: List[Callable[[Job], None]] = []
        self.job_failed_callbacks: List[Callable[[Job, str], None]] = []

    def start(self) -> None:
        """
        Start the scheduler.

        The scheduler runs in a separate thread and periodically
        checks for pending jobs to execute.
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        logger.info("Scheduler stopped")

    def is_running(self) -> bool:
        """
        Check if the scheduler is running.

        Returns:
            True if running, False otherwise
        """
        return self.running and bool(self.thread and self.thread.is_alive())

    def add_job_completed_callback(self, callback: Callable[[Job], None]) -> None:
        """
        Add a callback to be called when a job is completed.

        Args:
            callback: Function to call with the completed job
        """
        self.job_completed_callbacks.append(callback)

    def add_job_failed_callback(self, callback: Callable[[Job, str], None]) -> None:
        """
        Add a callback to be called when a job fails.

        Args:
            callback: Function to call with the failed job and error message
        """
        self.job_failed_callbacks.append(callback)

    def _run(self) -> None:
        """Main scheduler loop."""
        while self.running:
            try:
                self._check_jobs()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

            # Sleep for the check interval
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _check_jobs(self) -> None:
        """
        Check for pending jobs and execute them.
        
        This method finds all pending jobs and executes them in separate threads.
        """
        pending_jobs = self.job_manager.get_pending_jobs()
        if not pending_jobs:
            return

        logger.debug(f"Found {len(pending_jobs)} pending jobs")
        for job in pending_jobs:
            # Skip jobs that are already running
            if job.id in self.running_jobs:
                continue

            # Execute the job in a separate thread
            logger.info(f"Starting job: {job.name} (ID: {job.id})")
            self.job_manager.update_job_status(job.id, JobStatus.RUNNING)
            self.running_jobs.add(job.id)
            
            thread = threading.Thread(
                target=self._execute_job,
                args=(job,),
                daemon=True
            )
            thread.start()

    def _execute_job(self, job: Job) -> None:
        """
        Execute a job.

        Args:
            job: The job to execute
        """
        # Store the original job ID to ensure we can always remove it from running_jobs
        job_id = job.id
        
        try:
            # Load the scraper configuration
            config = config_manager.load_config(job.config_name)
            if not config:
                raise ValueError(f"Configuration '{job.config_name}' not found")

            # Create and run the scraper
            scraper = create_scraper(config)
            results = run_scraper(scraper, config)
            
            # Mark the job as completed
            job = self.job_manager.mark_job_completed(job_id)
            logger.info(f"Job completed: {job.name} (ID: {job.id})")
            
            # Call completion callbacks
            for callback in self.job_completed_callbacks:
                try:
                    callback(job)
                except Exception as e:
                    logger.error(f"Error in job completion callback: {e}")
                    
        except Exception as e:
            error_message = str(e)
            logger.error(f"Job failed: {job.name} (ID: {job_id}) - {error_message}")
            
            # Mark the job as failed
            job = self.job_manager.mark_job_failed(job_id, error_message)
            
            # Call failure callbacks
            for callback in self.job_failed_callbacks:
                try:
                    callback(job, error_message)
                except Exception as e:
                    logger.error(f"Error in job failure callback: {e}")
        finally:
            # Remove the job from running jobs using the original job ID
            self.running_jobs.remove(job_id)


# Singleton instance
_scheduler_instance: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """
    Get the singleton scheduler instance.

    Returns:
        The scheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = Scheduler()
    return _scheduler_instance 