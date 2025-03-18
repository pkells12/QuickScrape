# Troubleshooting Scheduling Issues

This guide addresses common issues with QuickScrape's job scheduling system.

## Jobs Not Running

### Problem: Scheduled jobs are not executing at the expected time

#### Check if the scheduler is running

```bash
quickscrape scheduler status
```

If the scheduler is not running, start it:

```bash
quickscrape scheduler start
```

#### Check job status

```bash
quickscrape job list
```

Make sure the job is:
- Listed in the output
- Shows "enabled" status
- Has the correct next run time

#### Verify system time

```bash
date
```

Ensure your system time is correct, as the scheduler uses it to determine when to run jobs.

#### Check job configuration

```bash
quickscrape job show JOB_ID
```

Verify that:
- The schedule type and timing are correct
- The configuration file referenced exists
- The job is enabled

#### Look for error logs

```bash
quickscrape job logs JOB_ID
quickscrape scheduler logs
```

These logs may reveal issues that prevented the job from running.

#### Test the configuration manually

```bash
quickscrape scrape CONFIG_NAME
```

If the manual scrape fails, fix those issues first.

## Scheduler Not Starting

### Problem: The scheduler fails to start or keeps crashing

#### Check for error messages

```bash
quickscrape scheduler logs
```

Common issues include:
- Port conflicts
- Insufficient permissions
- Memory issues

#### Verify file permissions

Ensure QuickScrape has write access to its configuration directory:

```bash
ls -la ~/.quickscrape
```

#### Check for conflicting processes

```bash
ps aux | grep quickscrape
```

Multiple scheduler instances can cause problems.

#### Try running in debug mode

```bash
export QUICKSCRAPE_LOG_LEVEL=DEBUG
quickscrape scheduler start
```

This provides more detailed logs that can help identify the issue.

#### Restart with clean state

```bash
quickscrape scheduler stop --force
rm ~/.quickscrape/scheduler.state  # Backup this file first if needed
quickscrape scheduler start
```

## Jobs Failing Consistently

### Problem: Jobs start but consistently fail to complete

#### Check the job logs for specific errors

```bash
quickscrape job logs JOB_ID
```

Common errors include:
- Connection timeouts
- Selector not found (website structure changed)
- Authentication failures
- Memory issues

#### Test the configuration manually

```bash
quickscrape scrape CONFIG_NAME --verbose
```

This can provide immediate feedback on issues.

#### Check website availability

Test if the target website is accessible:

```bash
curl -I TARGET_URL
```

#### Verify resource usage

```bash
top -n 1
df -h
```

Ensure your system has sufficient CPU, memory, and disk space.

#### Adjust retry settings

If jobs fail due to temporary issues, increase the retry count:

```bash
quickscrape job update JOB_ID --max-retries 5 --retry-delay 300
```

#### Update selectors if the website changed

If the website structure changed, update your configuration:

```bash
quickscrape wizard --config CONFIG_NAME
```

## Schedule Timing Issues

### Problem: Jobs run at unexpected times

#### Check timezone settings

```bash
date
timedatectl  # On Linux systems
```

The scheduler uses local system time.

#### Verify cron expression

For custom schedules using cron expressions, use an online cron expression validator to verify your expression is correct.

#### Check for daylight saving time issues

Schedules may shift by an hour during daylight saving time transitions.

#### Examine job next run time

```bash
quickscrape job list
```

Compare the displayed next run time with your expectations.

## Database/Storage Issues

### Problem: Job history or state not being saved correctly

#### Check disk space

```bash
df -h
```

#### Verify file permissions

```bash
ls -la ~/.quickscrape/jobs/
```

#### Repair job database

```bash
quickscrape maintenance repair-jobs
```

This command will attempt to fix any corruption in the job database.

## Callback Issues

### Problem: Success or failure callbacks not executing

#### Check callback command permissions

Ensure the callback scripts or commands have execute permissions:

```bash
chmod +x /path/to/your/callback_script.sh
```

#### Test callback manually

```bash
/path/to/your/callback_script.sh
```

#### Check callback output in logs

```bash
quickscrape job logs JOB_ID
```

Look for any errors related to callback execution.

## System Service Issues

### Problem: Scheduler service not starting properly

#### Check service status

```bash
# For systemd
sudo systemctl status quickscrape

# For other systems
sudo service quickscrape status
```

#### Examine service logs

```bash
sudo journalctl -u quickscrape
```

#### Verify service configuration

For systemd:
```bash
cat /etc/systemd/system/quickscrape.service
```

Ensure paths, user permissions, and environment variables are correct.

## Recovery Steps

If you're experiencing persistent scheduling issues:

1. **Backup your data**:
   ```bash
   cp -r ~/.quickscrape ~/.quickscrape.backup
   ```

2. **Reset the scheduler**:
   ```bash
   quickscrape scheduler stop --force
   rm ~/.quickscrape/scheduler.state
   quickscrape scheduler start
   ```

3. **Recreate problematic jobs**:
   ```bash
   quickscrape job delete PROBLEM_JOB_ID
   quickscrape job create --config CONFIG_NAME --schedule TYPE
   ```

4. **Consider environment issues**:
   - If running in a container, ensure the container doesn't stop
   - On laptops, power management might interrupt the scheduler
   - Network connectivity issues can affect scheduled jobs

## Prevention

To avoid scheduling issues in the future:

1. **Monitor job status regularly**:
   ```bash
   quickscrape job list
   ```

2. **Set up notifications**:
   ```bash
   quickscrape job update JOB_ID --on-failure /path/to/notification_script.sh
   ```

3. **Run the scheduler as a proper system service**
4. **Keep QuickScrape updated**
5. **Implement regular configuration validation**
6. **Use appropriate retry settings for each job** 