"""
Job management models for QuickScrape.

This module contains Pydantic models that define the structure
for managing scraping jobs and their scheduling.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from quickscrape.config.models import ScraperConfig


class JobStatus(str, Enum):
    """
    Status of a scraping job.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class JobPriority(int, Enum):
    """
    Priority levels for jobs.
    """
    LOW = 1
    NORMAL = 2
    HIGH = 3


class ScheduleType(str, Enum):
    """
    Type of job schedule.
    """
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # For cron expressions


class JobSchedule(BaseModel):
    """
    Schedule configuration for a job.
    """
    type: ScheduleType = Field(..., description="Type of schedule")
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When to start the job"
    )
    end_time: Optional[datetime] = Field(
        None, description="When to stop scheduling the job (None for indefinite)"
    )
    repeat_interval: Optional[int] = Field(
        None, description="Interval for repeating the job (in appropriate units based on type)"
    )
    cron_expression: Optional[str] = Field(
        None, description="Cron expression for custom scheduling"
    )
    
    @validator("cron_expression")
    def validate_cron_for_custom_type(cls, v, values):
        """Validate that cron_expression is provided for custom schedule type."""
        if values.get("type") == ScheduleType.CUSTOM and not v:
            raise ValueError("cron_expression is required for custom schedule type")
        return v
    
    @validator("repeat_interval")
    def validate_repeat_interval(cls, v, values):
        """Validate that repeat_interval is provided for non-once schedules."""
        if values.get("type") != ScheduleType.ONCE and not v:
            raise ValueError(f"repeat_interval is required for schedule type: {values.get('type')}")
        return v


class Job(BaseModel):
    """
    Represents a scraping job.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique job ID")
    name: str = Field(..., description="Job name")
    config_name: str = Field(..., description="Name of the scraper configuration to use")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current status of the job")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="Job priority")
    schedule: Optional[JobSchedule] = Field(None, description="Schedule for the job")
    created_at: datetime = Field(default_factory=datetime.now, description="When the job was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the job was last updated")
    last_run: Optional[datetime] = Field(None, description="When the job was last run")
    next_run: Optional[datetime] = Field(None, description="When the job is scheduled to run next")
    run_count: int = Field(default=0, description="Number of times the job has been run")
    max_runs: Optional[int] = Field(None, description="Maximum number of times to run the job")
    retries: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    error_message: Optional[str] = Field(None, description="Error message if the job failed")
    
    def update_status(self, status: JobStatus) -> None:
        """
        Update the job status.
        
        Args:
            status: The new status to set
        """
        self.status = status
        self.updated_at = datetime.now()
    
    def increment_run_count(self) -> None:
        """Increment the run count and update the last_run timestamp."""
        self.run_count += 1
        self.last_run = datetime.now()
        self.updated_at = datetime.now()
    
    def increment_retries(self) -> None:
        """Increment the retry count."""
        self.retries += 1
        self.updated_at = datetime.now()
    
    def set_error(self, error_message: str) -> None:
        """
        Set an error message and update status to FAILED.
        
        Args:
            error_message: The error message to store
        """
        self.error_message = error_message
        self.update_status(JobStatus.FAILED) 