"""
Tests for job manager functionality.

This module tests the job management functionality of QuickScrape,
ensuring that jobs can be created, updated, and deleted correctly.
"""

import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, TYPE_CHECKING

import pytest
from pytest_mock import MockerFixture

from quickscrape.scheduling.models import Job, JobStatus, JobSchedule, ScheduleType
from quickscrape.scheduling.job_manager import JobManager

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def temp_jobs_dir() -> str:
    """
    Create a temporary directory for job files.
    
    Returns:
        Path to the temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def job_manager(temp_jobs_dir: str) -> JobManager:
    """
    Create a job manager instance with a temporary directory.
    
    Args:
        temp_jobs_dir: Path to temporary jobs directory
        
    Returns:
        Initialized job manager
    """
    return JobManager(jobs_dir=temp_jobs_dir)


@pytest.fixture
def mock_config_manager(monkeypatch: "MonkeyPatch") -> None:
    """
    Mock the config manager for testing.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    def mock_config_exists(config_name: str) -> bool:
        return True
    
    monkeypatch.setattr(
        "quickscrape.config.config_manager.config_exists", 
        mock_config_exists
    )


def test_create_job(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test creating a new job.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create a job
    job = job_manager.create_job("Test Job", "test_config")
    
    # Check that the job was created with the correct properties
    assert job.name == "Test Job"
    assert job.config_name == "test_config"
    assert job.status == JobStatus.PENDING
    assert job.id is not None
    
    # Check that the job was saved to disk
    job_path = os.path.join(job_manager.jobs_dir, f"{job.id}.json")
    assert os.path.exists(job_path)


def test_create_scheduled_job(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test creating a scheduled job.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create a schedule
    start_time = datetime.now() + timedelta(hours=1)
    schedule = JobSchedule(
        type=ScheduleType.DAILY,
        start_time=start_time,
        repeat_interval=1
    )
    
    # Create a job with the schedule
    job = job_manager.create_job("Scheduled Job", "test_config", schedule)
    
    # Check that the job was created with the correct properties
    assert job.name == "Scheduled Job"
    assert job.config_name == "test_config"
    assert job.status == JobStatus.SCHEDULED
    assert job.schedule is not None
    assert job.schedule.type == ScheduleType.DAILY
    assert job.schedule.start_time == start_time
    assert job.schedule.repeat_interval == 1
    assert job.next_run == start_time


def test_get_job(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test retrieving a job by ID.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create a job
    job = job_manager.create_job("Test Job", "test_config")
    
    # Retrieve the job
    retrieved_job = job_manager.get_job(job.id)
    
    # Check that the retrieved job matches the created job
    assert retrieved_job is not None
    assert retrieved_job.id == job.id
    assert retrieved_job.name == job.name
    assert retrieved_job.config_name == job.config_name


def test_get_jobs(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test retrieving all jobs.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create multiple jobs
    job1 = job_manager.create_job("Job 1", "config1")
    job2 = job_manager.create_job("Job 2", "config2")
    job3 = job_manager.create_job("Job 3", "config1")
    
    # Set different statuses
    job_manager.update_job_status(job2.id, JobStatus.RUNNING)
    
    # Retrieve all jobs
    all_jobs = job_manager.get_jobs()
    assert len(all_jobs) == 3
    
    # Retrieve jobs by status
    pending_jobs = job_manager.get_jobs(status=JobStatus.PENDING)
    assert len(pending_jobs) == 2
    assert all(job.status == JobStatus.PENDING for job in pending_jobs)
    
    running_jobs = job_manager.get_jobs(status=JobStatus.RUNNING)
    assert len(running_jobs) == 1
    assert running_jobs[0].id == job2.id
    
    # Retrieve jobs by config name
    config1_jobs = job_manager.get_jobs(config_name="config1")
    assert len(config1_jobs) == 2
    assert all(job.config_name == "config1" for job in config1_jobs)


def test_update_job(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test updating a job.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create a job
    job = job_manager.create_job("Test Job", "test_config")
    
    # Update the job
    updated_job = job_manager.update_job(
        job.id, 
        name="Updated Job",
        max_runs=5
    )
    
    # Check that the job was updated
    assert updated_job is not None
    assert updated_job.name == "Updated Job"
    assert updated_job.max_runs == 5
    
    # Retrieve the job to ensure it was saved
    retrieved_job = job_manager.get_job(job.id)
    assert retrieved_job is not None
    assert retrieved_job.name == "Updated Job"
    assert retrieved_job.max_runs == 5


def test_delete_job(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test deleting a job.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create a job
    job = job_manager.create_job("Test Job", "test_config")
    
    # Delete the job
    success = job_manager.delete_job(job.id)
    
    # Check that the job was deleted
    assert success
    assert job_manager.get_job(job.id) is None
    
    # Check that the job file was deleted
    job_path = os.path.join(job_manager.jobs_dir, f"{job.id}.json")
    assert not os.path.exists(job_path)


def test_mark_job_completed(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test marking a job as completed.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create a job
    job = job_manager.create_job("Test Job", "test_config")
    
    # Mark the job as completed
    updated_job = job_manager.mark_job_completed(job.id)
    
    # Check that the job was updated
    assert updated_job is not None
    assert updated_job.status == JobStatus.COMPLETED
    assert updated_job.run_count == 1
    assert updated_job.last_run is not None
    
    # Retrieve the job to ensure it was saved
    retrieved_job = job_manager.get_job(job.id)
    assert retrieved_job is not None
    assert retrieved_job.status == JobStatus.COMPLETED
    assert retrieved_job.run_count == 1
    assert retrieved_job.last_run is not None


def test_mark_job_failed(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test marking a job as failed.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create a job
    job = job_manager.create_job("Test Job", "test_config")
    
    # Mark the job as failed
    error_message = "Test error message"
    updated_job = job_manager.mark_job_failed(job.id, error_message)
    
    # Check that the job was updated
    assert updated_job is not None
    assert updated_job.status == JobStatus.SCHEDULED  # First retry, so scheduled
    assert updated_job.retries == 1
    assert updated_job.error_message == error_message
    
    # Mark as failed until it exceeds max retries (should be max+1 calls total)
    for _ in range(updated_job.max_retries):
        updated_job = job_manager.mark_job_failed(job.id, error_message)
    
    # Check that the job is now failed after exceeding max retries
    assert updated_job.status == JobStatus.FAILED
    
    # Retrieve the job to ensure it was saved
    retrieved_job = job_manager.get_job(job.id)
    assert retrieved_job is not None
    assert retrieved_job.status == JobStatus.FAILED
    # The retries should equal max_retries + 1 (initial retry + additional retries)
    assert retrieved_job.retries == retrieved_job.max_retries + 1
    assert retrieved_job.error_message == error_message


def test_get_pending_jobs(job_manager: JobManager, mock_config_manager: None) -> None:
    """
    Test retrieving pending jobs.
    
    Args:
        job_manager: Job manager fixture
        mock_config_manager: Mocked config manager
    """
    # Create jobs with different statuses
    job1 = job_manager.create_job("Job 1", "config1")  # PENDING
    job2 = job_manager.create_job("Job 2", "config2")
    job_manager.update_job_status(job2.id, JobStatus.RUNNING)
    job3 = job_manager.create_job("Job 3", "config3")
    job_manager.update_job_status(job3.id, JobStatus.COMPLETED)
    
    # Create a scheduled job with next_run in the past
    schedule_past = JobSchedule(
        type=ScheduleType.ONCE,
        start_time=datetime.now() - timedelta(hours=1)
    )
    job4 = job_manager.create_job("Job 4", "config4", schedule_past)
    
    # Create a scheduled job with next_run in the future
    schedule_future = JobSchedule(
        type=ScheduleType.ONCE,
        start_time=datetime.now() + timedelta(hours=1)
    )
    job5 = job_manager.create_job("Job 5", "config5", schedule_future)
    
    # Retrieve pending jobs
    pending_jobs = job_manager.get_pending_jobs()
    
    # Should include job1 (PENDING) and job4 (SCHEDULED with past next_run)
    assert len(pending_jobs) == 2
    pending_job_ids = [job.id for job in pending_jobs]
    assert job1.id in pending_job_ids
    assert job4.id in pending_job_ids
    assert job2.id not in pending_job_ids  # RUNNING
    assert job3.id not in pending_job_ids  # COMPLETED
    assert job5.id not in pending_job_ids  # SCHEDULED with future next_run 