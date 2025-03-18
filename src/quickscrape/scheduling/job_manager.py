"""
Job manager implementation for QuickScrape.

This module provides functionality for creating, updating, and managing
scraping jobs. It handles job persistence, status updates, and scheduling.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from quickscrape.config import config_manager
from quickscrape.scheduling.models import Job, JobStatus, JobSchedule
from quickscrape.utils.logger import get_logger

logger = get_logger(__name__)


class JobManager:
    """
    Manages scraping jobs for QuickScrape.

    Responsible for job CRUD operations, job status management,
    and job persistence.
    """

    def __init__(self, jobs_dir: Optional[str] = None) -> None:
        """
        Initialize the job manager.

        Args:
            jobs_dir: Directory to store job files (defaults to ~/.quickscrape/jobs)
        """
        self.jobs_dir = jobs_dir or os.path.join(
            config_manager.get_config_dir(), "jobs"
        )
        self._ensure_jobs_dir()
        self.jobs: Dict[str, Job] = {}
        self._load_jobs()

    def _ensure_jobs_dir(self) -> None:
        """Create the jobs directory if it doesn't exist."""
        os.makedirs(self.jobs_dir, exist_ok=True)

    def _load_jobs(self) -> None:
        """Load all jobs from disk."""
        jobs_path = Path(self.jobs_dir)
        if not jobs_path.exists():
            return

        for job_file in jobs_path.glob("*.json"):
            try:
                with open(job_file, "r") as f:
                    job_data = json.load(f)
                    job = Job.parse_obj(job_data)
                    self.jobs[job.id] = job
            except Exception as e:
                logger.error(f"Failed to load job from {job_file}: {e}")

    def _save_job(self, job: Job) -> None:
        """
        Save a job to disk.

        Args:
            job: The job to save
        """
        job_path = os.path.join(self.jobs_dir, f"{job.id}.json")
        try:
            with open(job_path, "w") as f:
                f.write(job.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to save job {job.id}: {e}")

    def create_job(self, 
                  name: str, 
                  config_name: str, 
                  schedule: Optional[JobSchedule] = None) -> Job:
        """
        Create a new job.

        Args:
            name: Name of the job
            config_name: Name of the scraper configuration to use
            schedule: Optional schedule for the job

        Returns:
            The created job

        Raises:
            ValueError: If config_name doesn't exist
        """
        # Verify that the config exists
        if not config_manager.config_exists(config_name):
            raise ValueError(f"Configuration '{config_name}' does not exist")

        job = Job(
            name=name,
            config_name=config_name,
            schedule=schedule
        )
        
        if schedule:
            job.update_status(JobStatus.SCHEDULED)
            # Set the next run time based on the schedule
            job.next_run = schedule.start_time

        self.jobs[job.id] = job
        self._save_job(job)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.

        Args:
            job_id: ID of the job to retrieve

        Returns:
            The job, or None if not found
        """
        return self.jobs.get(job_id)

    def get_jobs(self, 
                status: Optional[JobStatus] = None, 
                config_name: Optional[str] = None) -> List[Job]:
        """
        Get all jobs, optionally filtered by status and/or config name.

        Args:
            status: Optional status to filter by
            config_name: Optional config name to filter by

        Returns:
            List of jobs matching the filters
        """
        result = list(self.jobs.values())
        
        if status:
            result = [job for job in result if job.status == status]
            
        if config_name:
            result = [job for job in result if job.config_name == config_name]
            
        return result

    def update_job(self, job_id: str, **kwargs: Any) -> Optional[Job]:
        """
        Update a job with new values.

        Args:
            job_id: ID of the job to update
            **kwargs: Fields to update

        Returns:
            The updated job, or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        # Update the specified fields
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        job.updated_at = datetime.now()
        self._save_job(job)
        return job

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: ID of the job to delete

        Returns:
            True if the job was deleted, False otherwise
        """
        job = self.get_job(job_id)
        if not job:
            return False

        # Remove the job file
        job_path = os.path.join(self.jobs_dir, f"{job_id}.json")
        try:
            if os.path.exists(job_path):
                os.remove(job_path)
        except Exception as e:
            logger.error(f"Failed to delete job file {job_path}: {e}")

        # Remove from memory
        del self.jobs[job_id]
        return True

    def update_job_status(self, job_id: str, status: JobStatus) -> Optional[Job]:
        """
        Update a job's status.

        Args:
            job_id: ID of the job to update
            status: New status to set

        Returns:
            The updated job, or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.update_status(status)
        self._save_job(job)
        return job

    def mark_job_completed(self, job_id: str) -> Optional[Job]:
        """
        Mark a job as completed.

        Args:
            job_id: ID of the job to mark as completed

        Returns:
            The updated job, or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.increment_run_count()
        job.update_status(JobStatus.COMPLETED)
        
        # Update the next run time if it's a scheduled job
        if job.schedule and (job.max_runs is None or job.run_count < job.max_runs):
            self._update_next_run_time(job)
        
        self._save_job(job)
        return job

    def mark_job_failed(self, job_id: str, error_message: str) -> Optional[Job]:
        """
        Mark a job as failed with an error message.

        Args:
            job_id: ID of the job to mark as failed
            error_message: Error message describing the failure

        Returns:
            The updated job, or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.increment_retries()
        job.set_error(error_message)
        
        # If we haven't exceeded max retries, schedule another run
        if job.retries < job.max_retries:
            job.update_status(JobStatus.SCHEDULED)
            # We could implement backoff strategy here
        else:
            job.update_status(JobStatus.FAILED)
        
        self._save_job(job)
        return job

    def get_pending_jobs(self) -> List[Job]:
        """
        Get all jobs that are pending execution.

        Returns:
            List of pending jobs
        """
        now = datetime.now()
        return [
            job for job in self.jobs.values()
            if job.status == JobStatus.PENDING or
               (job.status == JobStatus.SCHEDULED and
                job.next_run and job.next_run <= now)
        ]
        
    def _update_next_run_time(self, job: Job) -> None:
        """
        Update a job's next run time based on its schedule.
        
        Args:
            job: The job to update
        """
        if not job.schedule:
            return
            
        schedule = job.schedule
        last_run = job.last_run or datetime.now()
        
        if schedule.type == "once":
            # One-time jobs don't have a next run
            job.next_run = None
            return
            
        # Calculate the next run time based on the schedule type
        if schedule.type == "daily":
            from datetime import timedelta
            days = schedule.repeat_interval or 1
            job.next_run = last_run + timedelta(days=days)
            
        elif schedule.type == "weekly":
            from datetime import timedelta
            weeks = schedule.repeat_interval or 1
            job.next_run = last_run + timedelta(weeks=weeks)
            
        elif schedule.type == "monthly":
            # Simple implementation - not handling month boundaries perfectly
            from dateutil.relativedelta import relativedelta
            months = schedule.repeat_interval or 1
            job.next_run = last_run + relativedelta(months=months)
            
        elif schedule.type == "custom" and schedule.cron_expression:
            # For custom cron expressions, we'd use a cron parser
            # This is a placeholder - in a real implementation, you'd use a library
            # like croniter to calculate the next run time
            job.next_run = last_run  # Placeholder 