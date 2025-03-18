# Examples

This section provides real-world examples of using QuickScrape for various web scraping tasks.

## Basic Examples

- [Scraping a Product Catalog](product-catalog.md)
- [Extracting News Articles](news-articles.md)
- [Collecting Contact Information](contact-info.md)
- [Working with Tables](data-tables.md)

## Advanced Examples

- [Handling Authentication](authentication.md)
- [Dealing with JavaScript-Heavy Sites](javascript-sites.md)
- [Bypassing Anti-Bot Measures](anti-bot.md)
- [Complex Pagination](complex-pagination.md)

## Job Scheduling Examples

- [Setting Up Daily Scrapes](daily-scrapes.md)
- [Creating Custom Schedules](custom-schedules.md)
- [Using Job Callbacks](job-callbacks.md)
- [Implementing Error Recovery](error-recovery.md)

## Data Processing Examples

- [Custom Data Cleaning](data-cleaning.md)
- [Post-Processing Scraped Data](post-processing.md)
- [Combining Multiple Scrapes](combining-data.md)
- [Data Validation](data-validation.md)

## Integration Examples

- [Using QuickScrape with Pandas](pandas-integration.md)
- [Sending Results to APIs](api-integration.md)
- [Database Storage](database-storage.md)
- [Email Notifications](email-notifications.md)

## Quick Reference

### Basic Scraping Command

```bash
quickscrape scrape my_config
```

### Creating a Scheduled Job

```bash
quickscrape job create --config my_config --schedule daily --at "09:00"
```

### Exporting to Different Formats

```bash
quickscrape scrape my_config --output-format excel
quickscrape scrape my_config --output-format json
quickscrape scrape my_config --output-format csv
quickscrape scrape my_config --output-format sqlite
```

### Using the Wizard

```bash
quickscrape wizard
```

See individual example pages for more detailed explanations and complete code samples. 