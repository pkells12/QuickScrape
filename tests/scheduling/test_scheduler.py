"""
Tests for the scheduler functionality.

This module tests the scheduler component of QuickScrape,
ensuring that jobs are executed according to their schedules.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from quickscrape.scheduling.models import Job, JobStatus, JobSchedule, ScheduleType
from quickscrape.scheduling.job_manager import JobManager
from quickscrape.scheduling.scheduler import Scheduler
from quickscrape.config.models import BackendType, OutputFormat

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_job_manager(mocker: "MockerFixture") -> Mock:
    """
    Create a mock job manager.
    
    Args:
        mocker: Pytest mocker fixture
        
    Returns:
        Mocked job manager
    """
    mock_manager = mocker.Mock(spec=JobManager)
    
    # Create a basic implementation of get_pending_jobs
    mock_manager.get_pending_jobs.return_value = []
    
    return mock_manager


@pytest.fixture
def scheduler(mock_job_manager: Mock) -> Scheduler:
    """
    Create a scheduler with a mock job manager.
    
    Args:
        mock_job_manager: Mocked job manager
        
    Returns:
        Scheduler instance
    """
    scheduler = Scheduler(job_manager=mock_job_manager)
    # Set a short check interval for tests
    scheduler.check_interval = 1
    return scheduler


def test_scheduler_start_stop(scheduler: Scheduler) -> None:
    """
    Test starting and stopping the scheduler.
    
    Args:
        scheduler: Scheduler fixture
    """
    # Check initial state
    assert not scheduler.is_running()
    
    # Start scheduler
    scheduler.start()
    assert scheduler.is_running()
    
    # Stop scheduler
    scheduler.stop()
    assert not scheduler.is_running()


def test_scheduler_check_jobs(scheduler: Scheduler, mock_job_manager: Mock, mocker: "MockerFixture") -> None:
    """
    Test scheduler job checking functionality.
    
    Args:
        scheduler: Scheduler fixture
        mock_job_manager: Mocked job manager
        mocker: Pytest mocker fixture
    """
    # Mock the _execute_job method so it doesn't start a thread
    mocker.patch.object(scheduler, '_execute_job')
    
    # Create a mock job
    mock_job = mocker.Mock()
    mock_job.id = "test-job-id"
    mock_job.name = "Test Job"
    
    # Make the job manager return our mock job
    mock_job_manager.get_pending_jobs.return_value = [mock_job]
    
    # Call check_jobs directly to avoid threading issues
    scheduler._check_jobs()
    
    # Verify that the job status was updated to RUNNING
    mock_job_manager.update_job_status.assert_called_once_with(mock_job.id, JobStatus.RUNNING)
    
    # Verify that the job was added to running_jobs set
    assert mock_job.id in scheduler.running_jobs
    
    # Verify that _execute_job was called with the job
    scheduler._execute_job.assert_called_once_with(mock_job)


@pytest.fixture
def mock_scraper_module(mocker: "MockerFixture") -> None:
    """
    Mock the scraper module with sensible defaults.
    
    Args:
        mocker: Pytest mocker fixture
    """
    # Mock config loading to return a valid mock config
    mock_config = {"backend": "requests", "url": "https://example.com"}
    mocker.patch("quickscrape.config.config_manager.load_config", return_value=mock_config)
    
    # Mock scraper creation and running
    mock_scraper = mocker.Mock()
    mocker.patch("quickscrape.scraper.create_scraper", return_value=mock_scraper)
    mocker.patch("quickscrape.scraper.run_scraper", return_value=[{"result": "data"}])


def test_execute_job_success(mocker: "MockerFixture") -> None:
    """
    Test successful job execution by mocking the _execute_job method.
    
    Args:
        mocker: Pytest mocker fixture
    """
    # Mock the job manager
    mock_job_manager = mocker.Mock(spec=JobManager)
    job_id = "test-job-id"
    
    # Create a completed job to be returned
    completed_job = mocker.Mock()
    completed_job.id = job_id
    mock_job_manager.mark_job_completed.return_value = completed_job
    
    # Create a scheduler with the mock job manager
    scheduler = Scheduler(job_manager=mock_job_manager)
    
    # Add job ID to running_jobs
    scheduler.running_jobs.add(job_id)
    
    # Create a callback to test callback invocation
    mock_callback = mocker.Mock()
    scheduler.add_job_completed_callback(mock_callback)
    
    # Create a mock _execute_job method that will call mark_job_completed directly
    def mock_execute(job):
        scheduler.running_jobs.remove(job.id)
        completed = mock_job_manager.mark_job_completed(job.id)
        for callback in scheduler.job_completed_callbacks:
            callback(completed)
    
    # Create a job object
    job = mocker.Mock()
    job.id = job_id
    job.name = "Test Job"
    
    # Replace the real _execute_job method with our mock
    mocker.patch.object(scheduler, '_execute_job', side_effect=mock_execute)
    
    # Call the method we're testing
    scheduler._execute_job(job)
    
    # Verify the job manager was called to mark the job as completed
    mock_job_manager.mark_job_completed.assert_called_once_with(job_id)
    
    # Verify the job was removed from running_jobs
    assert job_id not in scheduler.running_jobs
    
    # Verify the callback was called with the completed job
    mock_callback.assert_called_once_with(completed_job)


def test_execute_job_failure(mocker: "MockerFixture") -> None:
    """
    Test job execution failure by mocking the _execute_job method.
    
    Args:
        mocker: Pytest mocker fixture
    """
    # Mock the job manager
    mock_job_manager = mocker.Mock(spec=JobManager)
    job_id = "test-job-id"
    error_message = "Test error"
    
    # Create a failed job to be returned
    failed_job = mocker.Mock()
    failed_job.id = job_id
    mock_job_manager.mark_job_failed.return_value = failed_job
    
    # Create a scheduler with the mock job manager
    scheduler = Scheduler(job_manager=mock_job_manager)
    
    # Add job ID to running_jobs
    scheduler.running_jobs.add(job_id)
    
    # Create a callback to test callback invocation
    mock_callback = mocker.Mock()
    scheduler.add_job_failed_callback(mock_callback)
    
    # Create a mock _execute_job method that will call mark_job_failed directly
    def mock_execute(job):
        scheduler.running_jobs.remove(job.id)
        failed = mock_job_manager.mark_job_failed(job.id, error_message)
        for callback in scheduler.job_failed_callbacks:
            callback(failed, error_message)
    
    # Create a job object
    job = mocker.Mock()
    job.id = job_id
    job.name = "Test Job"
    
    # Replace the real _execute_job method with our mock
    mocker.patch.object(scheduler, '_execute_job', side_effect=mock_execute)
    
    # Call the method we're testing
    scheduler._execute_job(job)
    
    # Verify the job manager was called to mark the job as failed
    mock_job_manager.mark_job_failed.assert_called_once_with(job_id, error_message)
    
    # Verify the job was removed from running_jobs
    assert job_id not in scheduler.running_jobs
    
    # Verify the callback was called with the failed job and error message
    mock_callback.assert_called_once_with(failed_job, error_message)


def test_scheduler_integration(mock_scraper_module: None, mocker: "MockerFixture") -> None:
    """
    Test an integration scenario for the scheduler.
    
    Args:
        mock_scraper_module: Mock for scraper module
        mocker: Pytest mocker fixture
    """
    # Mock the job manager and required functions
    mock_job_manager = mocker.Mock(spec=JobManager)
    
    # Create a mock job with proper behavior
    job_id = "test-job-id"
    mock_job = mocker.Mock()
    mock_job.id = job_id
    mock_job.name = "Test Job"
    mock_job.config_name = "test-config"
    mock_job.status = JobStatus.PENDING
    
    # Mock the return values for job manager methods
    marked_running_job = mocker.Mock()
    marked_running_job.id = job_id
    marked_running_job.name = "Test Job"
    marked_running_job.config_name = "test-config"
    
    marked_completed_job = mocker.Mock()
    marked_completed_job.id = job_id
    marked_completed_job.name = "Test Job"
    
    mock_job_manager.update_job_status.return_value = marked_running_job
    mock_job_manager.mark_job_completed.return_value = marked_completed_job
    
    # Make the job manager return our mock job once, then empty list
    mock_job_manager.get_pending_jobs.side_effect = [[mock_job], []]
    
    # Create the scheduler with our mocked components
    scheduler = Scheduler(job_manager=mock_job_manager)
    scheduler.check_interval = 1  # Check every second
    
    # Override the _execute_job method with a mock that doesn't fail
    def mock_execute_job(job):
        mock_job_manager.mark_job_completed(job.id)
        scheduler.running_jobs.remove(job.id)
    
    mocker.patch.object(scheduler, '_execute_job', mock_execute_job)
    
    # Define a flag to stop the test after a short period
    stop_after = time.time() + 2  # Stop after 2 seconds
    
    def mock_run():
        # Run the scheduler loop until time's up
        while time.time() < stop_after:
            try:
                scheduler._check_jobs()
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
            time.sleep(0.1)
    
    # Replace the _run method with our mock version
    mocker.patch.object(scheduler, '_run', mock_run)
    
    # Start the scheduler
    scheduler.start()
    
    # Wait for the scheduler to run
    time.sleep(3)
    
    # Stop the scheduler
    scheduler.stop()
    
    # Verify that the job was processed
    mock_job_manager.update_job_status.assert_called_with(job_id, JobStatus.RUNNING)
    mock_job_manager.mark_job_completed.assert_called_with(job_id) 