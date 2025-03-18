# Job Scheduling

QuickScrape includes a powerful job scheduling system that allows you to run scraping tasks on a regular basis without manual intervention. This guide explains how to create, manage, and monitor scheduled jobs.

## Job Management Basics

### Creating a Job

You can create a scheduled job using the `job create` command:

```bash
quickscrape job create --config my_config --schedule daily
```

This will create a job that runs the `my_config` scraping configuration once per day.

### Basic Schedule Types

QuickScrape supports several predefined schedule types:

- `once`: Run the job once at a specified time
- `hourly`: Run the job every hour
- `daily`: Run the job once per day
- `weekly`: Run the job once per week
- `monthly`: Run the job once per month

### Listing Jobs

To see all your scheduled jobs:

```bash
quickscrape job list
```

This displays a table with all jobs, their statuses, next run times, and other details.

### Deleting a Job

To remove a scheduled job:

```bash
quickscrape job delete JOB_ID
```

Replace `JOB_ID` with the ID shown in the job list.

## Advanced Scheduling

### Custom Schedules

For more control, you can use cron-style expressions to define custom schedules:

```bash
quickscrape job create --config my_config --cron "0 9 * * 1-5"
```

This example creates a job that runs at 9:00 AM Monday through Friday.

Cron expression format:
```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of the month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of the week (0-6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

### Time-specific Jobs

You can specify exactly when a job should run:

```bash
quickscrape job create --config my_config --schedule daily --at "08:30"
```

This creates a job that runs daily at 8:30 AM.

### Date-specific Jobs

For one-time jobs on a specific date:

```bash
quickscrape job create --config my_config --schedule once --date "2024-06-15" --at "14:00"
```

This creates a job that runs once on June 15, 2024, at 2:00 PM.

## Job Execution Options

### Output Customization

You can specify custom output options for scheduled jobs:

```bash
quickscrape job create --config my_config --schedule daily \
  --output-format csv --output-path "/data/daily_scrapes/{date}.csv"
```

The `{date}` placeholder will be replaced with the current date when the job runs.

### Retry Settings

Configure automatic retries for failed jobs:

```bash
quickscrape job create --config my_config --schedule daily \
  --max-retries 3 --retry-delay 300
```

This sets up to 3 retries with a 5-minute delay between attempts.

### Job Callbacks

You can configure jobs to trigger actions on completion or failure:

```bash
quickscrape job create --config my_config --schedule daily \
  --on-success "notify_success.sh" --on-failure "notify_failure.sh"
```

These could be scripts that send notifications or perform other actions.

## Managing the Scheduler

### Starting the Scheduler

Start the scheduler to execute jobs according to their schedules:

```bash
quickscrape scheduler start
```

The scheduler runs in the background and executes jobs at their scheduled times.

### Checking Scheduler Status

Check if the scheduler is running:

```bash
quickscrape scheduler status
```

### Stopping the Scheduler

Stop the scheduler when needed:

```bash
quickscrape scheduler stop
```

This will gracefully shut down the scheduler, allowing any running jobs to complete.

### Running in Daemon Mode

For production use, you can run the scheduler as a daemon:

```bash
quickscrape scheduler start --daemon
```

### Running with System Service

For more reliable operation, you can set up the scheduler as a system service:

#### Systemd (Linux)

Create a systemd service file at `/etc/systemd/system/quickscrape.service`:

```ini
[Unit]
Description=QuickScrape Scheduler
After=network.target

[Service]
ExecStart=/usr/local/bin/quickscrape scheduler start
User=your_username
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:

```bash
sudo systemctl enable quickscrape
sudo systemctl start quickscrape
```

## Monitoring Jobs

### Job Logs

View logs for a specific job:

```bash
quickscrape job logs JOB_ID
```

### Job History

View execution history for a job:

```bash
quickscrape job history JOB_ID
```

This shows past runs, their statuses, durations, and any error messages.

### Running a Job Manually

You can run a scheduled job immediately, regardless of its schedule:

```bash
quickscrape job run JOB_ID
```

## Troubleshooting Scheduled Jobs

### Common Issues

1. **Job not running at expected time**:
   - Check if the scheduler is running: `quickscrape scheduler status`
   - Verify the job's next run time: `quickscrape job list`
   - Check system time and timezone: `date`

2. **Job fails consistently**:
   - Check job logs: `quickscrape job logs JOB_ID`
   - Test the configuration manually: `quickscrape scrape CONFIG_NAME`
   - Verify the website is still accessible

3. **Scheduler stops unexpectedly**:
   - Check system logs: `journalctl -u quickscrape`
   - Set up the scheduler as a system service for better reliability

### Best Practices

1. **Start small**: Begin with a few jobs before scaling up
2. **Monitor resource usage**: Ensure your system can handle the load
3. **Use appropriate intervals**: Avoid scraping too frequently
4. **Set up notifications**: Configure callbacks to alert you of failures
5. **Regularly check job status**: Use `quickscrape job list` to monitor your jobs

## Next Steps

- [Learn about CLI usage](cli-usage.md)
- [Explore advanced usage options](advanced-usage.md)
- [Understand ethical scraping practices](ethical-scraping.md) 