# API Reference

This section provides detailed documentation for QuickScrape's API components. It's intended for developers who want to integrate QuickScrape into their own applications or extend its functionality.

## Main Modules

- [Core Module](core.md) - Core functionality and base classes
- [Scraper Module](scraper.md) - Web scraping implementation
- [Config Module](config.md) - Configuration management
- [Export Module](export.md) - Data export functionality
- [Job Management Module](job-management.md) - Job scheduling and management
- [CLI Module](cli.md) - Command-line interface implementation
- [API Client Module](api-client.md) - Claude API integration

## Using QuickScrape Programmatically

QuickScrape can be used as a Python library in your own code:

```python
import quickscrape
from quickscrape.config import ConfigManager
from quickscrape.scraper import ScraperFactory
from quickscrape.export import ExporterFactory

# Load a configuration
config_manager = ConfigManager()
config = config_manager.load_config("my_config")

# Create a scraper
scraper_factory = ScraperFactory()
scraper = scraper_factory.create_scraper(config)

# Run the scrape
results = scraper.scrape()

# Export the results
exporter_factory = ExporterFactory()
exporter = exporter_factory.create_exporter(config.output.format)
exporter.export(results, config.output.path)
```

## Job Management API

The job management system can be used programmatically:

```python
from quickscrape.scheduling import JobManager, Scheduler, JobSchedule

# Create a job manager
job_manager = JobManager()

# Create a job
job_schedule = JobSchedule.daily(time="09:00")
job = job_manager.create_job(
    config_name="my_config",
    schedule=job_schedule,
    description="Daily scrape at 9 AM"
)

# Start the scheduler
scheduler = Scheduler(job_manager)
scheduler.start()
```

## Integration Points

QuickScrape provides several extension points:

- Custom Scraper Backends
- Custom Data Exporters
- Custom Selector Generators
- Job Callbacks

Check the specific module documentation for details on how to extend each component.

## API Stability

The public API components documented here follow semantic versioning:

- **Stable API** - These components will maintain backward compatibility within a major version
- **Experimental API** - These components may change between minor versions
- **Internal API** - These components are not intended for public use and may change at any time

Each module documentation notes the stability level of its components. 