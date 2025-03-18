"""
Terminal-based setup wizard for QuickScrape.

This module provides an interactive wizard that guides users through the process
of creating scraping configurations step by step.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, cast

import inquirer
import requests
from bs4 import BeautifulSoup
from pydantic import ValidationError
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from quickscrape.config import config_manager
from quickscrape.config.models import (
    BackendType,
    OutputConfig,
    OutputFormat,
    PaginationConfig,
    PaginationType,
    ScraperConfig,
)
from quickscrape.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


def run_wizard(config_name: Optional[str] = None) -> None:
    """
    Run the interactive setup wizard.

    Guides the user through creating a scraping configuration by asking questions
    and showing previews of the data that will be extracted.

    Args:
        config_name: The name for the new configuration. If None, will prompt the user.

    Returns:
        None
    """
    console.print(
        Panel.fit(
            "Welcome to the QuickScrape Setup Wizard!", 
            title="QuickScrape", 
            subtitle="Interactive Configuration"
        )
    )
    
    console.print(Markdown(
        "This wizard will guide you through setting up a scraping configuration. "
        "You'll need to provide:\n\n"
        "1. The URL to scrape\n"
        "2. CSS selectors for data to extract\n"
        "3. Pagination settings (if needed)\n"
        "4. Output format and location\n"
    ))
    
    if config_name is None:
        config_name = _prompt_for_config_name()
    
    # Check if configuration already exists
    if config_manager.config_exists(config_name):
        overwrite = inquirer.confirm(
            message=f"Configuration '{config_name}' already exists. Overwrite?",
            default=False
        )
        if not overwrite:
            console.print("[yellow]Wizard cancelled. Existing configuration not modified.[/yellow]")
            return
    
    # Start collecting configuration information
    url = _prompt_for_url()
    
    # If we can access the URL, try to help with selector creation
    selectors = _prompt_for_selectors(url)
    
    # Pagination settings
    pagination = _prompt_for_pagination()
    
    # Output configuration
    output = _prompt_for_output(config_name)
    
    # Backend selection
    backend = _prompt_for_backend()
    
    # Advanced options
    wait_time, user_agent, headers = _prompt_for_advanced_options()
    
    # Create and save the configuration
    try:
        config = ScraperConfig(
            url=url,
            selectors=selectors,
            backend=backend,
            wait_time=wait_time,
            user_agent=user_agent,
            headers=headers,
            pagination=pagination,
            output=output
        )
        
        # Save the configuration
        config_manager.save_config(config, config_name)
        
        console.print(
            f"\n[bold green]Configuration '{config_name}' created successfully![/bold green]"
        )
        console.print(
            f"To run this configuration, use: [bold]quickscrape scrape {config_name}[/bold]"
        )
    except ValidationError as e:
        console.print("[bold red]Error creating configuration:[/bold red]")
        for error in e.errors():
            console.print(f"[red]- {error['loc'][0]}: {error['msg']}[/red]")
        console.print("\nPlease run the wizard again with correct values.")


def _prompt_for_config_name() -> str:
    """
    Prompt the user for a configuration name.
    
    Returns:
        str: The user-provided configuration name
    """
    while True:
        questions = [
            inquirer.Text(
                "config_name",
                message="Name for this scraping configuration",
                default="wizard_config"
            )
        ]
        answers = inquirer.prompt(questions)
        
        if not answers:
            # User pressed Ctrl+C
            console.print("[yellow]Wizard cancelled.[/yellow]")
            exit(0)
            
        config_name = answers["config_name"]
        
        # Basic validation - alphanumeric plus underscore and hyphen
        if not all(c.isalnum() or c in "_-" for c in config_name):
            console.print("[red]Configuration name must contain only letters, numbers, underscores, and hyphens.[/red]")
            continue
            
        return config_name


def _prompt_for_url() -> str:
    """
    Prompt the user for the URL to scrape.
    
    Returns:
        str: The user-provided URL
    """
    while True:
        questions = [
            inquirer.Text(
                "url",
                message="URL to scrape",
                default="https://example.com"
            )
        ]
        answers = inquirer.prompt(questions)
        
        if not answers:
            # User pressed Ctrl+C
            console.print("[yellow]Wizard cancelled.[/yellow]")
            exit(0)
            
        url = answers["url"]
        
        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            console.print("[red]URL must start with http:// or https://[/red]")
            continue
            
        # Check if URL is accessible
        try:
            console.print(f"[yellow]Testing connection to {url}...[/yellow]")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            console.print(f"[green]Successfully connected to {url}[/green]")
            return url
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error accessing URL: {str(e)}[/red]")
            retry = inquirer.confirm(
                message="Do you want to try a different URL?",
                default=True
            )
            if retry:
                continue
            else:
                # User wants to proceed with potentially inaccessible URL
                return url


def _prompt_for_selectors(url: str) -> Dict[str, str]:
    """
    Prompt the user for CSS selectors to extract data.
    
    Args:
        url: The URL to scrape, for potential automated help
        
    Returns:
        Dict[str, str]: Dictionary of field names to CSS selectors
    """
    console.print("\n[bold]Data Selection[/bold]")
    console.print("Define what data you want to extract using CSS selectors.")
    
    # Try to help the user by fetching the page and showing some common elements
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Show some common elements that might be of interest
        console.print("\n[bold]Some common elements found on the page:[/bold]")
        
        table = Table(show_header=True)
        table.add_column("Element Type")
        table.add_column("Count")
        table.add_column("Example Selector")
        
        elements = [
            ("Heading (h1)", "h1", soup.find_all("h1")),
            ("Heading (h2)", "h2", soup.find_all("h2")),
            ("Paragraph", "p", soup.find_all("p")),
            ("List item", "li", soup.find_all("li")),
            ("Link", "a", soup.find_all("a")),
            ("Image", "img", soup.find_all("img")),
            ("Table", "table", soup.find_all("table")),
            ("Div with class", "div[class]", soup.find_all("div", class_=True)),
        ]
        
        for name, selector, found in elements:
            if found:
                example = found[0].get("class", [])
                example_selector = selector
                if name == "Div with class" and example:
                    example_selector = f'div.{example[0]}'
                table.add_row(name, str(len(found)), example_selector)
        
        console.print(table)
        console.print(
            "\n[italic]These are just suggestions. You may need to inspect the page "
            "in your browser to find the exact selectors.[/italic]"
        )
    except Exception as e:
        logger.debug(f"Error analyzing page: {str(e)}")
        # Don't show error to user, just skip the helpful suggestions
    
    selectors: Dict[str, str] = {}
    adding = True
    
    while adding:
        # Prompt for a new field
        questions = [
            inquirer.Text(
                "field_name",
                message="Field name (e.g., title, price, description)"
            ),
            inquirer.Text(
                "selector",
                message="CSS selector (e.g., h1.title, span.price)"
            )
        ]
        answers = inquirer.prompt(questions)
        
        if not answers:
            # User pressed Ctrl+C
            console.print("[yellow]Wizard cancelled.[/yellow]")
            exit(0)
            
        field_name = answers["field_name"]
        selector = answers["selector"]
        
        if field_name and selector:
            selectors[field_name] = selector
            
            # Show current selectors
            console.print("\n[bold]Current selectors:[/bold]")
            for name, sel in selectors.items():
                console.print(f"[green]{name}:[/green] {sel}")
            
            # Ask if they want to add more
            adding = inquirer.confirm(
                message="Add another field?",
                default=True if len(selectors) < 3 else False
            )
        else:
            console.print("[yellow]Both field name and selector are required.[/yellow]")
    
    return selectors


def _prompt_for_pagination() -> Optional[PaginationConfig]:
    """
    Prompt the user for pagination settings.
    
    Returns:
        Optional[PaginationConfig]: Pagination configuration or None if not needed
    """
    console.print("\n[bold]Pagination Settings[/bold]")
    
    has_pagination = inquirer.confirm(
        message="Does the website have multiple pages of results to scrape?",
        default=False
    )
    
    if not has_pagination:
        return None
    
    # Pagination type
    questions = [
        inquirer.List(
            "pagination_type",
            message="What type of pagination does the website use?",
            choices=[
                ("URL parameter (e.g., ?page=2)", PaginationType.URL_PARAM),
                ("Next button", PaginationType.NEXT_BUTTON),
                ("Load more button", PaginationType.LOAD_MORE),
                ("Infinite scroll", PaginationType.INFINITE_SCROLL)
            ]
        )
    ]
    answers = inquirer.prompt(questions)
    
    if not answers:
        # User pressed Ctrl+C
        console.print("[yellow]Wizard cancelled.[/yellow]")
        exit(0)
        
    pagination_type = cast(PaginationType, answers["pagination_type"])
    
    # Different follow-up questions based on pagination type
    pagination_config: Dict[str, Any] = {"type": pagination_type}
    
    if pagination_type == PaginationType.URL_PARAM:
        questions = [
            inquirer.Text(
                "param_name",
                message="URL parameter name",
                default="page"
            )
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            console.print("[yellow]Wizard cancelled.[/yellow]")
            exit(0)
        pagination_config["param_name"] = answers["param_name"]
        
    elif pagination_type in [PaginationType.NEXT_BUTTON, PaginationType.LOAD_MORE]:
        questions = [
            inquirer.Text(
                "selector",
                message="CSS selector for the button",
                default="a.next-page" if pagination_type == PaginationType.NEXT_BUTTON else "button.load-more"
            )
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            console.print("[yellow]Wizard cancelled.[/yellow]")
            exit(0)
        pagination_config["selector"] = answers["selector"]
    
    # Max pages for all pagination types
    questions = [
        inquirer.Text(
            "max_pages",
            message="Maximum number of pages to scrape (leave empty for unlimited)",
            default=""
        )
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        console.print("[yellow]Wizard cancelled.[/yellow]")
        exit(0)
    
    max_pages_str = answers["max_pages"]
    if max_pages_str and max_pages_str.isdigit():
        pagination_config["max_pages"] = int(max_pages_str)
    
    return PaginationConfig(**pagination_config)


def _prompt_for_output(config_name: str) -> OutputConfig:
    """
    Prompt the user for output settings.
    
    Args:
        config_name: The configuration name to use as default filename
        
    Returns:
        OutputConfig: The output configuration
    """
    console.print("\n[bold]Output Settings[/bold]")
    
    # Output format
    questions = [
        inquirer.List(
            "format",
            message="Output format",
            choices=[
                ("CSV (Comma-Separated Values)", OutputFormat.CSV),
                ("JSON (JavaScript Object Notation)", OutputFormat.JSON),
                ("Excel (.xlsx)", OutputFormat.EXCEL)
            ]
        )
    ]
    answers = inquirer.prompt(questions)
    
    if not answers:
        # User pressed Ctrl+C
        console.print("[yellow]Wizard cancelled.[/yellow]")
        exit(0)
        
    output_format = cast(OutputFormat, answers["format"])
    
    # File extension based on format
    extensions = {
        OutputFormat.CSV: ".csv",
        OutputFormat.JSON: ".json",
        OutputFormat.EXCEL: ".xlsx"
    }
    default_filename = f"{config_name}{extensions[output_format]}"
    
    # Output path
    questions = [
        inquirer.Text(
            "path",
            message="Output file path",
            default=os.path.join("output", default_filename)
        )
    ]
    answers = inquirer.prompt(questions)
    
    if not answers:
        console.print("[yellow]Wizard cancelled.[/yellow]")
        exit(0)
        
    output_path = answers["path"]
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        console.print(f"[green]Created output directory: {output_dir}[/green]")
    
    # Additional options based on format
    append = False
    delimiter = ","
    encoding = "utf-8"
    
    if output_format == OutputFormat.CSV:
        questions = [
            inquirer.Text(
                "delimiter",
                message="Delimiter",
                default=","
            )
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            console.print("[yellow]Wizard cancelled.[/yellow]")
            exit(0)
        delimiter = answers["delimiter"]
    
    # Append option for all formats
    append = inquirer.confirm(
        message="Append to existing file if it exists?",
        default=False
    )
    
    return OutputConfig(
        format=output_format,
        path=output_path,
        append=append,
        delimiter=delimiter,
        encoding=encoding
    )


def _prompt_for_backend() -> BackendType:
    """
    Prompt the user for the scraping backend.
    
    Returns:
        BackendType: The selected backend type
    """
    console.print("\n[bold]Scraping Backend[/bold]")
    
    questions = [
        inquirer.List(
            "backend",
            message="Select scraping backend",
            choices=[
                ("Auto-detect (recommended)", BackendType.AUTO),
                ("Requests (simple, no JavaScript support)", BackendType.REQUESTS),
                ("Playwright (supports JavaScript, needs browser)", BackendType.PLAYWRIGHT)
            ]
        )
    ]
    answers = inquirer.prompt(questions)
    
    if not answers:
        # User pressed Ctrl+C
        console.print("[yellow]Wizard cancelled.[/yellow]")
        exit(0)
        
    return cast(BackendType, answers["backend"])


def _prompt_for_advanced_options() -> Tuple[float, Optional[str], Optional[Dict[str, str]]]:
    """
    Prompt the user for advanced options.
    
    Returns:
        Tuple[float, Optional[str], Optional[Dict[str, str]]]: 
            wait_time, user_agent, headers
    """
    console.print("\n[bold]Advanced Options[/bold]")
    
    # Default wait time
    questions = [
        inquirer.Text(
            "wait_time",
            message="Wait time between requests (seconds)",
            default="0.5"
        )
    ]
    answers = inquirer.prompt(questions)
    
    if not answers:
        # User pressed Ctrl+C
        console.print("[yellow]Wizard cancelled.[/yellow]")
        exit(0)
        
    try:
        wait_time = float(answers["wait_time"])
    except ValueError:
        console.print("[yellow]Invalid wait time, using default (0.5s)[/yellow]")
        wait_time = 0.5
    
    # User agent
    use_custom_ua = inquirer.confirm(
        message="Use a custom User-Agent string?",
        default=False
    )
    
    user_agent = None
    if use_custom_ua:
        questions = [
            inquirer.Text(
                "user_agent",
                message="User-Agent string",
                default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            console.print("[yellow]Wizard cancelled.[/yellow]")
            exit(0)
        user_agent = answers["user_agent"]
    
    # Custom headers
    use_custom_headers = inquirer.confirm(
        message="Add custom HTTP headers?",
        default=False
    )
    
    headers = None
    if use_custom_headers:
        headers = {}
        adding_headers = True
        
        while adding_headers:
            questions = [
                inquirer.Text("header_name", message="Header name"),
                inquirer.Text("header_value", message="Header value")
            ]
            answers = inquirer.prompt(questions)
            
            if not answers:
                console.print("[yellow]Wizard cancelled.[/yellow]")
                exit(0)
                
            header_name = answers["header_name"]
            header_value = answers["header_value"]
            
            if header_name and header_value:
                headers[header_name] = header_value
                
                # Show current headers
                console.print("\n[bold]Current headers:[/bold]")
                for name, value in headers.items():
                    console.print(f"[green]{name}:[/green] {value}")
                
                # Ask if they want to add more
                adding_headers = inquirer.confirm(
                    message="Add another header?",
                    default=False
                )
            else:
                console.print("[yellow]Both header name and value are required.[/yellow]")
    
    return wait_time, user_agent, headers 