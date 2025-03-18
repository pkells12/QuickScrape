# CLI Usage Guide

QuickScrape offers a comprehensive command-line interface (CLI) for all operations. This guide covers the available commands, options, and provides examples.

## Command Structure

The QuickScrape CLI follows this general structure:

```
quickscrape [COMMAND] [SUBCOMMAND] [OPTIONS] [ARGUMENTS]
```

## Getting Help

To see the main help information:

```bash
quickscrape --help
```

To get help for a specific command:

```bash
quickscrape [COMMAND] --help
```

## Core Commands

### Initialize

Initialize QuickScrape in the current user's home directory:

```bash
quickscrape init
```

Options:
- `--directory PATH`: Specify a custom directory instead of the default `~/.quickscrape`
- `--force`: Overwrite existing configuration directory if it exists

### Wizard

Launch the interactive setup wizard:

```bash
quickscrape wizard
```

Options:
- `--name NAME`: Pre-set the configuration name
- `--url URL`: Pre-set the target URL
- `--output FORMAT`: Pre-set the output format

### Scrape

Run a scraping job using a saved configuration:

```bash
quickscrape scrape CONFIG_NAME
```

Options:
- `--output-format FORMAT`: Override the output format (csv, json, excel, sqlite)
- `--output-path PATH`: Override the output file path
- `--max-pages N`: Limit the number of pages to scrape
- `--verbose`: Show detailed progress information
- `--quiet`: Suppress all output except errors
- `--delay SECONDS`: Add a delay between requests
- `--timeout SECONDS`: Set request timeout
- `--user-agent AGENT`: Use a custom user agent
- `--backend BACKEND`: Override the scraping backend (requests, cloudscraper, playwright)

### List

List available configurations:

```bash
quickscrape list
```

Options:
- `--format FORMAT`: Output format (table, json, yaml)

### Validate

Validate a configuration file:

```bash
quickscrape validate CONFIG_NAME
```

Options:
- `--fix`: Attempt to fix common issues

## Job Management Commands

### Job Create

Create a new scheduled job:

```bash
quickscrape job create --config CONFIG_NAME --schedule SCHEDULE
```

Required options:
- `--config CONFIG_NAME`: Name of the scraping configuration to use

Schedule options (one is required):
- `--schedule TYPE`: Predefined schedule type (once, hourly, daily, weekly, monthly)
- `--cron EXPRESSION`: Custom cron expression (e.g., "0 9 * * 1-5")

Additional options:
- `--at TIME`: Specific time for the job (HH:MM format)
- `--date DATE`: Specific date for one-time jobs (YYYY-MM-DD format)
- `--max-retries N`: Number of times to retry on failure
- `--retry-delay SECONDS`: Delay between retry attempts
- `--output-format FORMAT`: Override output format
- `--output-path PATH`: Override output path
- `--on-success COMMAND`: Command to run on successful completion
- `--on-failure COMMAND`: Command to run on failure
- `--description TEXT`: Job description
- `--enabled`: Start the job as enabled (default)
- `--disabled`: Start the job as disabled

### Job List

List all scheduled jobs:

```bash
quickscrape job list
```

Options:
- `--format FORMAT`: Output format (table, json, yaml)
- `--status STATUS`: Filter by status (pending, running, completed, failed)
- `--config CONFIG_NAME`: Filter by configuration

### Job Show

Show details for a specific job:

```bash
quickscrape job show JOB_ID
```

Options:
- `--format FORMAT`: Output format (detailed, json, yaml)

### Job Update

Update an existing job:

```bash
quickscrape job update JOB_ID [OPTIONS]
```

Options:
- `--schedule TYPE`: Change schedule type
- `--cron EXPRESSION`: Change cron expression
- `--at TIME`: Change specific time
- `--max-retries N`: Change retry count
- `--retry-delay SECONDS`: Change retry delay
- `--description TEXT`: Change description
- `--enable`: Enable the job
- `--disable`: Disable the job

### Job Delete

Delete a scheduled job:

```bash
quickscrape job delete JOB_ID
```

Options:
- `--force`: Delete without confirmation

### Job Run

Run a job immediately:

```bash
quickscrape job run JOB_ID
```

Options:
- `--background`: Run in the background

### Job Logs

View logs for a specific job:

```bash
quickscrape job logs JOB_ID
```

Options:
- `--lines N`: Number of lines to show (default: 50)
- `--follow`: Follow log output in real-time

### Job History

View execution history for a job:

```bash
quickscrape job history JOB_ID
```

Options:
- `--limit N`: Limit number of history entries
- `--format FORMAT`: Output format (table, json, yaml)

## Scheduler Commands

### Scheduler Start

Start the job scheduler:

```bash
quickscrape scheduler start
```

Options:
- `--daemon`: Run as a background daemon
- `--log-file PATH`: Specify log file location

### Scheduler Stop

Stop the job scheduler:

```bash
quickscrape scheduler stop
```

Options:
- `--force`: Force stop even if jobs are running

### Scheduler Status

Check the status of the scheduler:

```bash
quickscrape scheduler status
```

Options:
- `--format FORMAT`: Output format (text, json, yaml)

### Scheduler Restart

Restart the scheduler:

```bash
quickscrape scheduler restart
```

## Configuration Commands

### Config Set

Set a configuration value:

```bash
quickscrape config set KEY VALUE
```

Example:
```bash
quickscrape config set default_output_dir ~/scrapes
```

### Config Get

Get a configuration value:

```bash
quickscrape config get KEY
```

Example:
```bash
quickscrape config get default_user_agent
```

### Config List

List all configuration values:

```bash
quickscrape config list
```

### Config Reset

Reset configuration to defaults:

```bash
quickscrape config reset
```

Options:
- `--key KEY`: Reset only a specific key

## Practical Examples

### Basic Scraping Workflow

```bash
# Initialize QuickScrape
quickscrape init

# Create a configuration with the wizard
quickscrape wizard

# Run the scraping job
quickscrape scrape my_first_config

# Create a daily scheduled job
quickscrape job create --config my_first_config --schedule daily --at "09:00"

# Start the scheduler
quickscrape scheduler start

# Check job status later
quickscrape job list
```

### Overriding Output Options

```bash
# Scrape with custom output options
quickscrape scrape product_scraper --output-format excel --output-path "~/exports/products_$(date +%F).xlsx"
```

### Debugging Scrapes

```bash
# Validate configuration
quickscrape validate product_scraper

# Run with verbose output
quickscrape scrape product_scraper --verbose
```

### Managing Jobs

```bash
# List all failed jobs
quickscrape job list --status failed

# Check the logs for a failed job
quickscrape job logs abc123

# Re-run a failed job
quickscrape job run abc123

# Disable a job temporarily
quickscrape job update abc123 --disable
```

## Environment Variables

QuickScrape also respects these environment variables:

- `QUICKSCRAPE_CONFIG_DIR`: Override the default configuration directory
- `QUICKSCRAPE_USER_AGENT`: Default user agent for requests
- `QUICKSCRAPE_DEFAULT_BACKEND`: Default scraping backend
- `QUICKSCRAPE_LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR)
- `QUICKSCRAPE_MAX_RETRIES`: Default max retries for failed requests
- `CLAUDE_API_KEY`: API key for Claude AI selector generation

You can set these in your environment or in a `.env` file in the QuickScrape directory.

## Next Steps

- [Learn about configuration options](configuration.md)
- [Understand job scheduling](scheduling.md)
- [Explore advanced usage options](advanced-usage.md) 