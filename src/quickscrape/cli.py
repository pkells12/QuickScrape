#!/usr/bin/env python
"""
CLI interface for QuickScrape.

This module provides the command-line interface for the QuickScrape tool,
allowing users to easily set up and run web scraping tasks.
"""

import os
import json
import sys
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

import click
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from quickscrape.config import config_manager
from quickscrape.config.init import initialize_config, create_example_configs
from quickscrape.config.list import list_configurations, get_config_details
from quickscrape.config.models import OutputFormat, ScraperConfig
from quickscrape.core import version
from quickscrape.utils.logger import configure_file_logging, get_logger, set_log_level
from quickscrape.cli.wizard import run_wizard
from quickscrape.scraper import create_scraper
from quickscrape.scheduling import JobManager, Scheduler, get_scheduler, JobSchedule, JobStatus, ScheduleType

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version=version.get_version())
@click.option(
    "--debug", is_flag=True, help="Enable debug logging"
)
@click.option(
    "--log-file", is_flag=True, help="Enable logging to a file"
)
def main(debug: bool, log_file: bool) -> None:
    """
    QuickScrape: A web scraping tool for novices.

    This tool helps you scrape data from websites without requiring
    advanced technical knowledge. Use the interactive wizard to
    set up scraping tasks or specify configurations manually.
    """
    # Configure logging based on options
    if debug:
        import logging
        set_log_level(logging.DEBUG)
        os.environ["QUICKSCRAPE_DEBUG"] = "1"
        logger.debug("Debug logging enabled")
    
    if log_file:
        configure_file_logging()
        logger.info("File logging enabled")


@main.command("init")
@click.argument("name", required=False, default="default")
@click.option(
    "--force", "-f", is_flag=True, help="Overwrite existing configuration if it exists"
)
@click.option(
    "--examples", is_flag=True, help="Create example configurations"
)
def init_command(name: str, force: bool, examples: bool) -> None:
    """
    Initialize a new scraping configuration.

    Creates a new configuration file with default settings
    that you can then customize for your scraping task.

    If NAME is not provided, the configuration will be named 'default'.
    """
    if examples:
        create_example_configs()
        return
    
    initialize_config(name, force)


@main.command("scrape")
@click.argument("config_name", required=True)
@click.option(
    "--output", "-o", help="Specify output file (overrides configuration setting)"
)
@click.option("--format", "-f", help="Specify output format (csv, json, excel)")
@click.option(
    "--debug", is_flag=True, help="Enable debug mode with detailed logging output"
)
def scrape_command(config_name: str, output: Optional[str], format: Optional[str], debug: bool) -> None:
    """
    Run a scraping job using the specified configuration.

    This command executes a scraping task based on the configuration
    specified by CONFIG_NAME. The configuration must exist in the
    QuickScrape configuration directory.

    Example:
    quickscrape scrape my_product_scraper
    """
    if debug:
        import logging
        set_log_level(logging.DEBUG)
        logger.debug("Debug mode enabled for scraping")
    
    # Load the configuration
    try:
        config = config_manager.load_config(config_name)
        logger.debug(f"Loaded configuration: {config_name}")
    except Exception as e:
        console.print(f"[bold red]Error loading configuration '{config_name}':[/bold red] {str(e)}")
        sys.exit(1)
    
    # Override output settings if provided
    if output:
        config.output.path = output
        logger.debug(f"Output path overridden to: {output}")
    
    if format:
        try:
            config.output.format = OutputFormat(format.lower())
            logger.debug(f"Output format overridden to: {format}")
        except ValueError:
            console.print(f"[bold yellow]Invalid output format: {format}. Using configuration default.[/bold yellow]")
    
    # Create and run the scraper
    try:
        console.print(Panel(f"Scraping [bold]{config.url}[/bold]", title="QuickScrape"))
        
        # Create the appropriate scraper based on the configuration
        scraper = create_scraper(config)
        
        # Run the scraper
        result = scraper.scrape()
        
        if not result.success:
            console.print(f"[bold red]Scraping failed:[/bold red] {result.error}")
            sys.exit(1)
        
        # Display summary
        console.print(f"\n[bold green]Scraping completed successfully![/bold green]")
        console.print(f"Scraped [bold]{result.total_items}[/bold] items from [bold]{result.pages_scraped}[/bold] pages")
        console.print(f"Duration: [bold]{result.duration_seconds:.2f}[/bold] seconds")
        
        # Save the results
        items = result.items
        if items:
            save_results(items, config)
            console.print(f"\nResults saved to [bold]{config.output.path}[/bold]")
            
            # Show a sample of the data
            display_sample_results(items)
        else:
            console.print("[bold yellow]No items found to save.[/bold yellow]")
    
    except Exception as e:
        logger.exception("Error during scraping")
        console.print(f"[bold red]Error during scraping:[/bold red] {str(e)}")
        sys.exit(1)


def save_results(items: List[Dict[str, Any]], config: ScraperConfig) -> None:
    """
    Save the scraping results to the specified output file.
    
    Args:
        items: The list of scraped items
        config: The scraper configuration
    """
    output_path = config.output.path
    output_format = config.output.format
    append_mode = config.output.append
    
    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.debug(f"Created output directory: {output_dir}")
    
    # Save according to the format
    if output_format == OutputFormat.CSV:
        save_as_csv(items, output_path, append_mode, config.output.delimiter)
    elif output_format == OutputFormat.JSON:
        save_as_json(items, output_path, append_mode)
    elif output_format == OutputFormat.EXCEL:
        save_as_excel(items, output_path)


def save_as_csv(items: List[Dict[str, Any]], path: str, append: bool, delimiter: str = ",") -> None:
    """
    Save items as a CSV file.
    
    Args:
        items: The list of items to save
        path: The output file path
        append: Whether to append to existing file
        delimiter: CSV delimiter character
    """
    mode = "a" if append and os.path.exists(path) else "w"
    write_header = mode == "w" or not os.path.exists(path)
    
    with open(path, mode, newline="", encoding="utf-8") as f:
        if items:
            writer = csv.DictWriter(f, fieldnames=items[0].keys(), delimiter=delimiter)
            if write_header:
                writer.writeheader()
            writer.writerows(items)


def save_as_json(items: List[Dict[str, Any]], path: str, append: bool) -> None:
    """
    Save items as a JSON file.
    
    Args:
        items: The list of items to save
        path: The output file path
        append: Whether to append to existing file
    """
    if append and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                
            if isinstance(existing_data, list):
                items = existing_data + items
        except json.JSONDecodeError:
            logger.warning(f"Could not parse existing JSON file: {path}. Creating new file.")
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def save_as_excel(items: List[Dict[str, Any]], path: str) -> None:
    """
    Save items as an Excel file.
    
    Args:
        items: The list of items to save
        path: The output file path
    """
    df = pd.DataFrame(items)
    df.to_excel(path, index=False, engine="openpyxl")


def display_sample_results(items: List[Dict[str, Any]], sample_size: int = 5) -> None:
    """
    Display a sample of the scraped results in a table.
    
    Args:
        items: The list of scraped items
        sample_size: Number of items to display
    """
    if not items:
        return
    
    # Create a table for displaying the results
    table = Table(title=f"Sample Results ({min(sample_size, len(items))} of {len(items)} items)")
    
    # Add columns based on the keys in the first item
    for key in items[0].keys():
        table.add_column(key)
    
    # Add rows for each item (up to sample_size)
    for item in items[:sample_size]:
        row = []
        for key in items[0].keys():
            value = item.get(key, "")
            # Truncate very long values
            if isinstance(value, str) and len(value) > 50:
                value = value[:47] + "..."
            row.append(str(value))
        table.add_row(*row)
    
    console.print("\n")
    console.print(table)


@main.command("wizard")
@click.argument("name", required=False)
def wizard_command(name: Optional[str]) -> None:
    """
    Start the interactive setup wizard.

    The wizard will guide you through the process of creating
    a scraping configuration by asking questions and showing
    previews of the data that will be extracted.

    If NAME is not provided, the configuration will be named 'wizard_config'.
    """
    run_wizard(name)


@main.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.argument("config_name", required=False)
def list_command(verbose: bool, config_name: Optional[str]) -> None:
    """
    List available configurations.

    Shows all the configured scraping jobs in your QuickScrape
    configuration directory, along with basic information about each.
    
    Use --verbose to see more details about each configuration.
    
    If CONFIG_NAME is provided, shows detailed information about that specific configuration.
    """
    if config_name:
        get_config_details(config_name)
    else:
        list_configurations(verbose)


@main.command()
def generate_selectors(
    url: str = click.Argument(..., help="URL to generate selectors for"),
    output: Optional[str] = click.Option(
        None, "--output", "-o", help="Path to save the generated selectors config"
    ),
    api_key: Optional[str] = click.Option(
        None, "--api-key", "-k", help="Claude API key (overrides environment variable)"
    ),
    model: str = click.Option(
        "claude-3-haiku-20240307", "--model", "-m", 
        help="Claude model to use (opus, sonnet, haiku)"
    ),
):
    """
    Generate CSS selectors from natural language descriptions.
    
    This command interactively prompts for natural language descriptions of elements
    to extract, then uses Claude AI to generate the appropriate CSS selectors.
    """
    try:
        import os
        from rich.prompt import Prompt, Confirm
        from rich.console import Console
        from rich.table import Table
        
        from quickscrape.api.selector_generator import SelectorGenerator
        from quickscrape.api.claude import ClaudeModel
        from quickscrape.config.models import ScraperConfig, OutputFormat
        
        console = Console()
        
        # Get API key
        api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            console.print("[bold red]Error:[/bold red] Claude API key required. Set CLAUDE_API_KEY environment variable or use --api-key option.")
            raise click.Exit(1)
        
        # Validate model name
        try:
            model_enum = ClaudeModel(model)
        except ValueError:
            console.print(f"[bold red]Error:[/bold red] Invalid model name: {model}")
            console.print(f"Available models: {', '.join([m.value for m in ClaudeModel])}")
            raise click.Exit(1)
        
        console.print(f"\n[bold blue]Generating selectors for[/bold blue] {url}")
        console.print("Enter natural language descriptions for elements you want to extract.")
        console.print("Enter an empty name to finish.\n")
        
        field_descriptions = {}
        while True:
            field_name = Prompt.ask("[bold]Element name[/bold] (empty to finish)")
            if not field_name:
                if not field_descriptions:
                    console.print("[yellow]Warning: No element descriptions provided.[/yellow]")
                    if not Confirm.ask("Continue without elements?"):
                        continue
                break
            
            description = Prompt.ask(f"[bold]Description for {field_name}[/bold]")
            field_descriptions[field_name] = description
        
        if field_descriptions:
            console.print("\n[bold green]Generating selectors using Claude AI...[/bold green]")
            
            try:
                selector_generator = SelectorGenerator(api_key=api_key)
                selectors = selector_generator.interactive_selector_generation(url, field_descriptions)
                
                # Display results
                console.print("\n[bold green]Generated Selectors:[/bold green]")
                table = Table(show_header=True)
                table.add_column("Field", style="bold")
                table.add_column("Description", style="dim")
                table.add_column("Generated Selector", style="cyan")
                
                for field, selector in selectors.items():
                    table.add_row(field, field_descriptions[field], selector)
                
                console.print(table)
                
                # Prompt to save config
                if Confirm.ask("\nSave as a scraper configuration?"):
                    output_path = output or Prompt.ask("Output file path", default="scraper_config.yaml")
                    output_format = OutputFormat.CSV
                    output_format_input = Prompt.ask(
                        "Output format", 
                        choices=[f.value for f in OutputFormat],
                        default=OutputFormat.CSV.value
                    )
                    output_format = OutputFormat(output_format_input)
                    
                    output_file = Prompt.ask("Output data file", default=f"output.{output_format.value}")
                    
                    # Create config
                    config = ScraperConfig(
                        url=url,
                        selectors=selectors,
                        selector_descriptions=field_descriptions,
                        output={
                            "format": output_format,
                            "path": output_file,
                        }
                    )
                    
                    # Save config
                    from quickscrape.config.config_manager import ConfigManager
                    config_manager = ConfigManager()
                    config_manager.save_config(output_path, config)
                    
                    console.print(f"[bold green]Configuration saved to:[/bold green] {output_path}")
            
            except Exception as e:
                console.print(f"[bold red]Error generating selectors:[/bold red] {str(e)}")
                raise click.Exit(1)
        
    except ImportError as e:
        print(f"Error: Required package not found: {e}")
        print("Make sure all dependencies are installed.")
        raise click.Exit(1)


@main.command()
def analyze_webpage(
    url: str = click.Argument(..., help="URL to analyze"),
    api_key: Optional[str] = click.Option(
        None, "--api-key", "-k", help="Claude API key (overrides environment variable)"
    ),
    model: str = click.Option(
        "claude-3-sonnet-20240229", "--model", "-m", 
        help="Claude model to use (opus, sonnet, haiku)"
    ),
):
    """
    Analyze a webpage and suggest data extraction points.
    
    This command uses Claude AI to analyze a webpage and suggest what kind of
    data might be worth extracting, along with natural language descriptions
    that can be used with the generate_selectors command.
    """
    try:
        import os
        import json
        from rich.console import Console
        from rich.markdown import Markdown
        import httpx
        
        from quickscrape.api.claude import ClaudeAPIClient, ClaudeConfig, ClaudeModel
        from quickscrape.scraper.factory import create_scraper
        
        console = Console()
        
        # Get API key
        api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            console.print("[bold red]Error:[/bold red] Claude API key required. Set CLAUDE_API_KEY environment variable or use --api-key option.")
            raise click.Exit(1)
        
        # Validate model name
        try:
            model_enum = ClaudeModel(model)
        except ValueError:
            console.print(f"[bold red]Error:[/bold red] Invalid model name: {model}")
            console.print(f"Available models: {', '.join([m.value for m in ClaudeModel])}")
            raise click.Exit(1)
        
        console.print(f"\n[bold blue]Analyzing webpage:[/bold blue] {url}")
        
        try:
            # Fetch the HTML content
            scraper = create_scraper(url)
            html_content = scraper.get_html(url)
            
            # Prepare Claude client
            claude_config = ClaudeConfig(
                api_key=api_key,
                model=model_enum,
                max_tokens=1000,
                temperature=0.0,
            )
            
            prompt = f"""
            Analyze this HTML and suggest key data elements that would be useful to extract for web scraping.
            
            HTML content:
            ```html
            {html_content[:20000]}  # Truncate to avoid token limits
            ```
            
            For each suggested element:
            1. Provide a descriptive field name (e.g., "product_title", "price", "rating")
            2. Write a natural language description of what to look for
            3. Suggest the most likely data type (text, number, date, URL, etc.)
            
            Return a JSON array of objects with keys: "field_name", "description", "data_type".
            
            Example:
            ```json
            [
                {{"field_name": "product_title", "description": "The main product name or title", "data_type": "text"}},
                {{"field_name": "price", "description": "The current product price including currency symbol", "data_type": "price"}}
            ]
            ```
            
            Return only the JSON. Do not include any explanation before or after.
            """
            
            # Send request to Claude
            with ClaudeAPIClient(config=claude_config) as claude_client:
                payload = {
                    "model": claude_config.model,
                    "max_tokens": claude_config.max_tokens,
                    "temperature": claude_config.temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                }
                
                response = claude_client.client.post("/v1/messages", json=payload)
                response.raise_for_status()
                
                data = response.json()
                result = data["content"][0]["text"].strip()
                
                # Parse the JSON result
                try:
                    suggestions = json.loads(result)
                    
                    # Display results
                    console.print("\n[bold green]Suggested Data Elements:[/bold green]")
                    
                    for item in suggestions:
                        console.print(f"\n[bold cyan]{item['field_name']}[/bold cyan] ([italic]{item['data_type']}[/italic])")
                        console.print(f"  {item['description']}")
                    
                    console.print("\n[bold blue]Next Steps:[/bold blue]")
                    console.print("Use these descriptions with the generate_selectors command to create CSS selectors:")
                    console.print(f"  quickscrape generate_selectors {url}")
                    
                except json.JSONDecodeError:
                    console.print("\n[bold yellow]Claude didn't return valid JSON. Here's the raw response:[/bold yellow]")
                    console.print(Markdown(result))
        
        except Exception as e:
            console.print(f"[bold red]Error analyzing webpage:[/bold red] {str(e)}")
            raise click.Exit(1)
        
    except ImportError as e:
        print(f"Error: Required package not found: {e}")
        print("Make sure all dependencies are installed.")
        raise click.Exit(1)


@main.group("job")
def job_group() -> None:
    """
    Manage scraping jobs.

    This group of commands allows you to create, list, run,
    and manage scraping jobs.
    """
    pass


@job_group.command("create")
@click.argument("name", required=True)
@click.argument("config_name", required=True)
@click.option(
    "--schedule-type", 
    type=click.Choice(['once', 'daily', 'weekly', 'monthly', 'custom']),
    help="Type of schedule for the job"
)
@click.option(
    "--start-time", 
    type=click.DateTime(formats=["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]),
    default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    help="When to start the job (format: YYYY-MM-DD HH:MM:SS)"
)
@click.option(
    "--repeat-interval", 
    type=int,
    help="Interval for repeating the job (days/weeks/months depending on schedule type)"
)
@click.option(
    "--cron-expression", 
    help="Cron expression for custom schedule type"
)
@click.option(
    "--max-runs", 
    type=int,
    help="Maximum number of times to run the job"
)
def create_job_command(
    name: str, 
    config_name: str, 
    schedule_type: Optional[str],
    start_time: Optional[datetime],
    repeat_interval: Optional[int],
    cron_expression: Optional[str],
    max_runs: Optional[int]
) -> None:
    """
    Create a new scraping job.

    Creates a job using NAME and CONFIG_NAME, with optional scheduling parameters.
    """
    job_manager = JobManager()
    
    # Create schedule if parameters are provided
    schedule = None
    if schedule_type:
        schedule_kwargs = {
            "type": ScheduleType(schedule_type),
            "start_time": start_time or datetime.now()
        }
        
        if repeat_interval is not None:
            schedule_kwargs["repeat_interval"] = repeat_interval
            
        if cron_expression:
            schedule_kwargs["cron_expression"] = cron_expression
            
        schedule = JobSchedule(**schedule_kwargs)
    
    try:
        job = job_manager.create_job(name, config_name, schedule)
        if max_runs is not None:
            job_manager.update_job(job.id, max_runs=max_runs)
            
        console.print(f"[green]Job created successfully.[/green]")
        console.print(f"Job ID: [bold]{job.id}[/bold]")
        console.print(f"Status: [bold]{job.status}[/bold]")
        if job.next_run:
            console.print(f"Next run: [bold]{job.next_run}[/bold]")
    except Exception as e:
        console.print(f"[red]Error creating job: {e}[/red]")
        sys.exit(1)


@job_group.command("list")
@click.option(
    "--status", 
    type=click.Choice(['pending', 'running', 'completed', 'failed', 'cancelled', 'scheduled']),
    help="Filter jobs by status"
)
@click.option(
    "--config", 
    help="Filter jobs by configuration name"
)
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    help="Show detailed information"
)
def list_jobs_command(
    status: Optional[str],
    config: Optional[str],
    verbose: bool
) -> None:
    """
    List all scraping jobs.
    
    Shows all jobs with their status, configuration, and schedule.
    """
    job_manager = JobManager()
    
    job_status = JobStatus(status) if status else None
    jobs = job_manager.get_jobs(status=job_status, config_name=config)
    
    if not jobs:
        console.print("[yellow]No jobs found.[/yellow]")
        return
    
    table = Table(title="Scraping Jobs")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Config", style="blue")
    table.add_column("Status", style="magenta")
    table.add_column("Runs", justify="right")
    table.add_column("Created", style="dim")
    table.add_column("Last Run", style="dim")
    table.add_column("Next Run", style="yellow")
    
    for job in jobs:
        table.add_row(
            job.id[:8],
            job.name,
            job.config_name,
            job.status,
            str(job.run_count),
            job.created_at.strftime("%Y-%m-%d %H:%M"),
            job.last_run.strftime("%Y-%m-%d %H:%M") if job.last_run else "-",
            job.next_run.strftime("%Y-%m-%d %H:%M") if job.next_run else "-"
        )
    
    console.print(table)
    
    if verbose and jobs:
        console.print("\n[bold]Job Details:[/bold]")
        for job in jobs:
            panel = Panel(
                f"ID: {job.id}\n"
                f"Name: {job.name}\n"
                f"Config: {job.config_name}\n"
                f"Status: {job.status}\n"
                f"Priority: {job.priority}\n"
                f"Run Count: {job.run_count}" + 
                (f" (max: {job.max_runs})" if job.max_runs else "") + "\n"
                f"Retries: {job.retries}/{job.max_retries}\n"
                f"Created: {job.created_at}\n"
                f"Last Run: {job.last_run or '-'}\n"
                f"Next Run: {job.next_run or '-'}\n" +
                (f"Error: {job.error_message}" if job.error_message else ""),
                title=job.name,
                border_style="green"
            )
            console.print(panel)


@job_group.command("run")
@click.argument("job_id", required=True)
def run_job_command(job_id: str) -> None:
    """
    Run a specific job immediately.
    
    Executes the job with JOB_ID immediately, regardless of its schedule.
    """
    job_manager = JobManager()
    job = job_manager.get_job(job_id)
    
    if not job:
        console.print(f"[red]Job with ID '{job_id}' not found.[/red]")
        return
    
    try:
        # Update job status to pending so it will be picked up by the scheduler
        job_manager.update_job_status(job_id, JobStatus.PENDING)
        console.print(f"[green]Job '{job.name}' queued for immediate execution.[/green]")
        
        # Start the scheduler if it's not already running
        scheduler = get_scheduler()
        if not scheduler.is_running():
            console.print("[yellow]Starting scheduler...[/yellow]")
            scheduler.start()
    except Exception as e:
        console.print(f"[red]Error running job: {e}[/red]")


@job_group.command("cancel")
@click.argument("job_id", required=True)
def cancel_job_command(job_id: str) -> None:
    """
    Cancel a specific job.
    
    Cancels the job with JOB_ID, preventing it from running.
    """
    job_manager = JobManager()
    job = job_manager.get_job(job_id)
    
    if not job:
        console.print(f"[red]Job with ID '{job_id}' not found.[/red]")
        return
    
    try:
        job_manager.update_job_status(job_id, JobStatus.CANCELLED)
        console.print(f"[green]Job '{job.name}' cancelled.[/green]")
    except Exception as e:
        console.print(f"[red]Error cancelling job: {e}[/red]")


@job_group.command("delete")
@click.argument("job_id", required=True)
@click.confirmation_option(prompt="Are you sure you want to delete this job?")
def delete_job_command(job_id: str) -> None:
    """
    Delete a specific job.
    
    Deletes the job with JOB_ID permanently.
    """
    job_manager = JobManager()
    job = job_manager.get_job(job_id)
    
    if not job:
        console.print(f"[red]Job with ID '{job_id}' not found.[/red]")
        return
    
    try:
        success = job_manager.delete_job(job_id)
        if success:
            console.print(f"[green]Job '{job.name}' deleted.[/green]")
        else:
            console.print(f"[red]Failed to delete job '{job.name}'.[/red]")
    except Exception as e:
        console.print(f"[red]Error deleting job: {e}[/red]")


@main.command("schedule")
@click.option(
    "--stop", 
    is_flag=True, 
    help="Stop the scheduler if it's running"
)
def schedule_command(stop: bool) -> None:
    """
    Start or stop the job scheduler.
    
    By default, starts the scheduler that will execute jobs based on their schedules.
    Use --stop to stop the scheduler.
    """
    scheduler = get_scheduler()
    
    if stop:
        if scheduler.is_running():
            scheduler.stop()
            console.print("[green]Scheduler stopped.[/green]")
        else:
            console.print("[yellow]Scheduler is not running.[/yellow]")
    else:
        if scheduler.is_running():
            console.print("[yellow]Scheduler is already running.[/yellow]")
        else:
            scheduler.start()
            console.print("[green]Scheduler started.[/green]")


if __name__ == "__main__":
    main() 