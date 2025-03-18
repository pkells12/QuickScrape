# Troubleshooting Guide

This guide helps you troubleshoot common issues with QuickScrape.

## Common Issues

### Installation Issues

- [Dependency Installation Failures](installation-issues.md#dependency-installation-failures)
- [Permission Errors](installation-issues.md#permission-errors)
- [Command Not Found Errors](installation-issues.md#command-not-found-errors)

### Configuration Issues

- [Invalid Configuration Format](configuration-issues.md#invalid-configuration-format)
- [Selector Not Found](configuration-issues.md#selector-not-found)
- [URL Connection Problems](configuration-issues.md#url-connection-problems)

### Scraping Issues

- [No Data Extracted](scraping-issues.md#no-data-extracted)
- [Incomplete Data](scraping-issues.md#incomplete-data)
- [Anti-Bot Measures Detected](scraping-issues.md#anti-bot-measures-detected)
- [JavaScript-Heavy Sites](scraping-issues.md#javascript-heavy-sites)

### Scheduling Issues

- [Jobs Not Running](scheduling-issues.md#jobs-not-running)
- [Scheduler Not Starting](scheduling-issues.md#scheduler-not-starting)
- [Jobs Failing Consistently](scheduling-issues.md#jobs-failing-consistently)

## General Troubleshooting Steps

1. **Check Logs**:
   ```bash
   quickscrape logs
   ```
   
2. **Enable Verbose Mode**:
   ```bash
   quickscrape scrape my_config --verbose
   ```

3. **Validate Configuration**:
   ```bash
   quickscrape validate my_config
   ```

4. **Check Dependencies**:
   ```bash
   pip list | grep -E "quickscrape|requests|playwright|beautifulsoup4"
   ```

5. **Test Website Accessibility**:
   ```bash
   curl -I https://example.com
   ```

6. **Update QuickScrape**:
   ```bash
   pip install --upgrade quickscrape
   ```

## Logging and Debugging

### Enabling Debug Logs

Set the log level to DEBUG for more detailed information:

```bash
export QUICKSCRAPE_LOG_LEVEL=DEBUG
quickscrape scrape my_config
```

### Viewing Job Logs

For scheduled jobs, check the specific job logs:

```bash
quickscrape job logs JOB_ID
```

### Checking Scheduler Logs

```bash
quickscrape scheduler logs
```

## Getting Help

If you're still having issues after following the troubleshooting steps:

1. **Check Documentation**: Review the full documentation for specific guidance.

2. **GitHub Issues**: Search existing issues on the GitHub repository to see if others have encountered the same problem.

3. **Open a New Issue**: If your problem is unique, open a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages and logs
   - Your environment details (OS, Python version, etc.)

4. **Community Support**: Check the community channels for help from other users.

## Common Error Messages

### "No module named 'quickscrape'"

This typically means the package isn't installed or isn't in your Python path. Try:

```bash
pip install quickscrape
```

### "Element not found: [selector]"

The selector specified in your configuration doesn't match any elements on the page. Check if:
- The website structure has changed
- Your selector is correct
- The content is loaded dynamically with JavaScript

### "Failed to establish connection"

Connection to the target website failed. Possible causes:
- Network issues
- Website is down
- IP blocking or rate limiting
- Firewall restrictions

### "Scheduler not running"

The job scheduler isn't running. Start it with:

```bash
quickscrape scheduler start
```

## Next Steps

- [Installation Issues](installation-issues.md)
- [Configuration Issues](configuration-issues.md)
- [Scraping Issues](scraping-issues.md)
- [Scheduling Issues](scheduling-issues.md) 