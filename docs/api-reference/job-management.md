# Job Management API

The Job Management API allows you to programmatically create, schedule, and manage scraping jobs. This is useful for integrating QuickScrape into your applications or automated workflows.

## API Stability

- **Stability:** Stable
- **Since Version:** 0.1.0

## Module Overview

```python
from quickscrape.scheduling import JobManager, Scheduler, Job, JobSchedule
```

## Core Classes

### JobManager

The `JobManager` class provides methods for creating, updating, and retrieving jobs.

```python
class JobManager:
    """Manages the creation, storage, and retrieval of scraping jobs."""
    
    def __init__(self, jobs_dir: Optional[str] = None) -> None:
        """Initialize the JobManager.
        
        Args:
            jobs_dir: Optional directory path for job storage.
                      Defaults to ~/.quickscrape/jobs/
        """
        
    def create_job(
        self,
        config_name: str,
        schedule: JobSchedule,
        description: Optional[str] = None,
        output_format: Optional[str] = None,
        output_path: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 300,
        on_success: Optional[str] = None,
        on_failure: Optional[str] = None,
        enabled: bool = True
    ) -> Job:
        """Create a new scraping job.
        
        Args:
            config_name: Name of the configuration to use for scraping
            schedule: JobSchedule object defining when the job should run
            description: Optional description of the job
            output_format: Optional format to override config format
            output_path: Optional path to override config output path
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Seconds to wait between retry attempts
            on_success: Optional command to run when job succeeds
            on_failure: Optional command to run when job fails
            enabled: Whether the job is enabled (default: True)
            
        Returns:
            Job: The created job object
        """
        
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by its ID.
        
        Args:
            job_id: The ID of the job to retrieve
            
        Returns:
            Job or None: The job if found, None otherwise
        """
        
    def update_job(self, job: Job) -> Job:
        """Update an existing job.
        
        Args:
            job: The modified job object
            
        Returns:
            Job: The updated job
        """
        
    def delete_job(self, job_id: str) -> bool:
        """Delete a job by its ID.
        
        Args:
            job_id: The ID of the job to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        
    def list_jobs(self) -> List[Job]:
        """List all jobs.
        
        Returns:
            List[Job]: List of all jobs
        """
        
    def filter_jobs(
        self, 
        status: Optional[str] = None,
        config_name: Optional[str] = None
    ) -> List[Job]:
        """Filter jobs by status or configuration.
        
        Args:
            status: Optional status to filter by
            config_name: Optional configuration name to filter by
            
        Returns:
            List[Job]: List of matching jobs
        """
```

### JobSchedule

The `JobSchedule` class represents when a job should run.

```python
class JobSchedule:
    """Represents a schedule for when a job should run."""
    
    @classmethod
    def once(cls, date: str, time: str) -> 'JobSchedule':
        """Create a one-time schedule.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            
        Returns:
            JobSchedule: A one-time schedule
        """
        
    @classmethod
    def hourly(cls, minute: int = 0) -> 'JobSchedule':
        """Create an hourly schedule.
        
        Args:
            minute: Minute of the hour to run (0-59)
            
        Returns:
            JobSchedule: An hourly schedule
        """
        
    @classmethod
    def daily(cls, time: str) -> 'JobSchedule':
        """Create a daily schedule.
        
        Args:
            time: Time in HH:MM format
            
        Returns:
            JobSchedule: A daily schedule
        """
        
    @classmethod
    def weekly(cls, day_of_week: int, time: str) -> 'JobSchedule':
        """Create a weekly schedule.
        
        Args:
            day_of_week: Day of the week (0=Monday, 6=Sunday)
            time: Time in HH:MM format
            
        Returns:
            JobSchedule: A weekly schedule
        """
        
    @classmethod
    def monthly(cls, day_of_month: int, time: str) -> 'JobSchedule':
        """Create a monthly schedule.
        
        Args:
            day_of_month: Day of the month (1-31)
            time: Time in HH:MM format
            
        Returns:
            JobSchedule: A monthly schedule
        """
        
    @classmethod
    def custom(cls, cron_expression: str) -> 'JobSchedule':
        """Create a custom schedule using a cron expression.
        
        Args:
            cron_expression: Standard cron expression (e.g., "0 9 * * 1-5")
            
        Returns:
            JobSchedule: A custom schedule
        """
        
    def get_next_run_time(self, from_time: Optional[datetime] = None) -> datetime:
        """Calculate the next time this schedule will run.
        
        Args:
            from_time: Base time to calculate from (default: now)
            
        Returns:
            datetime: The next run time
        """
```

### Job

The `Job` class represents a single scraping job.

```python
class Job:
    """Represents a scraping job."""
    
    id: str
    config_name: str
    schedule: JobSchedule
    description: Optional[str]
    output_format: Optional[str]
    output_path: Optional[str]
    max_retries: int
    retry_delay: int
    on_success: Optional[str]
    on_failure: Optional[str]
    enabled: bool
    status: str  # 'pending', 'running', 'completed', 'failed'
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    def run(self) -> bool:
        """Run the job immediately.
        
        Returns:
            bool: True if successful, False otherwise
        """
        
    def enable(self) -> None:
        """Enable the job."""
        
    def disable(self) -> None:
        """Disable the job."""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the job
        """
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create a job from a dictionary.
        
        Args:
            data: Dictionary representation of a job
            
        Returns:
            Job: The created job
        """
```

### Scheduler

The `Scheduler` class manages running jobs according to their schedules.

```python
class Scheduler:
    """Manages the execution of scheduled jobs."""
    
    def __init__(self, job_manager: JobManager) -> None:
        """Initialize the scheduler.
        
        Args:
            job_manager: JobManager instance to manage jobs
        """
        
    def start(self) -> None:
        """Start the scheduler."""
        
    def stop(self) -> None:
        """Stop the scheduler."""
        
    def is_running(self) -> bool:
        """Check if the scheduler is running.
        
        Returns:
            bool: True if running, False otherwise
        """
        
    def get_status(self) -> Dict[str, Any]:
        """Get the scheduler status.
        
        Returns:
            Dict[str, Any]: Status information
        """
```

## Usage Examples

### Creating and Starting a Job

```python
from quickscrape.scheduling import JobManager, JobSchedule, Scheduler

# Create a job manager
job_manager = JobManager()

# Create a daily job that runs at 9:00 AM
schedule = JobSchedule.daily(time="09:00")
job = job_manager.create_job(
    config_name="product_scraper",
    schedule=schedule,
    description="Daily product price scrape",
    output_format="csv",
    output_path="products_{date}.csv",
    max_retries=3,
    retry_delay=300,
    on_success="/path/to/success_script.sh",
    on_failure="/path/to/failure_script.sh"
)

print(f"Created job with ID: {job.id}")

# Start the scheduler
scheduler = Scheduler(job_manager)
scheduler.start()
```

### Managing Existing Jobs

```python
from quickscrape.scheduling import JobManager

# Create a job manager
job_manager = JobManager()

# List all jobs
jobs = job_manager.list_jobs()
for job in jobs:
    print(f"Job {job.id}: {job.description} (Next run: {job.next_run})")

# Get a specific job
job = job_manager.get_job("abc123")
if job:
    # Update the job
    job.max_retries = 5
    job.description = "Updated description"
    job_manager.update_job(job)
    print(f"Updated job {job.id}")

# Delete a job
job_manager.delete_job("xyz789")
```

### Custom Schedule with Cron Expression

```python
from quickscrape.scheduling import JobManager, JobSchedule

# Create a job manager
job_manager = JobManager()

# Create a custom schedule that runs at 9:00 AM on weekdays
schedule = JobSchedule.custom(cron_expression="0 9 * * 1-5")
job = job_manager.create_job(
    config_name="news_scraper",
    schedule=schedule,
    description="Weekday news scraping"
)

print(f"Next run time: {job.next_run}")
```

### Running a Job Manually

```python
from quickscrape.scheduling import JobManager

# Create a job manager
job_manager = JobManager()

# Get a job
job = job_manager.get_job("abc123")
if job:
    # Run the job immediately
    success = job.run()
    if success:
        print("Job ran successfully")
    else:
        print("Job failed")
```

## Notes

- Jobs are stored as JSON files in the `~/.quickscrape/jobs/` directory by default
- The scheduler uses APScheduler internally to manage job scheduling
- The scheduler needs to be running for jobs to execute automatically
- When using job callbacks, ensure the callback scripts have execute permissions 