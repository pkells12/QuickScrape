"""
Utilities for listing and displaying configurations.

This module provides functionality to list and display QuickScrape
configurations in a formatted way.
"""

import os
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table

from quickscrape.config import config_manager
from quickscrape.utils.logger import get_logger
from quickscrape.utils.yaml_utils import pydantic_model_to_yaml, yaml_safe_dump

logger = get_logger(__name__)
console = Console()


def list_configurations(verbose: bool = False) -> None:
    """
    List all available scraping configurations.

    Displays a formatted table of configurations with basic information.
    With verbose mode, shows more details about each configuration.

    Args:
        verbose: Whether to show detailed information about each configuration
    """
    # Get the list of configurations
    config_names = config_manager.list_configs()
    
    if not config_names:
        console.print(
            "[yellow]No configurations found.[/] Use [bold]quickscrape init[/] to create one."
        )
        return
    
    # Create a table to display the configurations
    if verbose:
        table = _create_verbose_table(config_names)
    else:
        table = _create_simple_table(config_names)
    
    # Print the table
    console.print(table)
    console.print(f"\nFound [bold]{len(config_names)}[/] configuration(s).")
    console.print("Use [bold]quickscrape init --examples[/] to create example configurations.")


def _create_simple_table(config_names: List[str]) -> Table:
    """
    Create a simple table with basic configuration information.

    Args:
        config_names: List of configuration names

    Returns:
        Table: A Rich Table object with basic configuration information
    """
    table = Table(title="Available Scraping Configurations")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Selectors", style="yellow")
    table.add_column("Output Format", style="magenta")
    
    for name in sorted(config_names):
        config = config_manager.load_config(name)
        if config:
            selectors_count = len(config.selectors) if config.selectors else 0
            
            table.add_row(
                name,
                config.url,
                str(selectors_count),
                config.output.format.value if config.output and config.output.format else "N/A"
            )
        else:
            table.add_row(name, "[red]Invalid configuration[/]", "", "")
    
    return table


def _create_verbose_table(config_names: List[str]) -> Table:
    """
    Create a detailed table with verbose configuration information.

    Args:
        config_names: List of configuration names

    Returns:
        Table: A Rich Table object with detailed configuration information
    """
    table = Table(title="Available Scraping Configurations (Detailed)")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Backend", style="blue")
    table.add_column("Selectors", style="yellow")
    table.add_column("Pagination", style="red")
    table.add_column("Output", style="magenta")
    
    for name in sorted(config_names):
        config = config_manager.load_config(name)
        if config:
            # Format selectors
            selectors = ", ".join(config.selectors.keys()) if config.selectors else "None"
            
            # Format pagination
            if config.pagination and config.pagination.type:
                pagination = f"{config.pagination.type.value}"
                if config.pagination.max_pages:
                    pagination += f" (max: {config.pagination.max_pages})"
            else:
                pagination = "None"
            
            # Format output
            output = f"{config.output.format.value} → {config.output.path}" if config.output else "N/A"
            
            table.add_row(
                name,
                config.url,
                config.backend.value,
                selectors,
                pagination,
                output
            )
        else:
            table.add_row(name, "[red]Invalid configuration[/]", "", "", "", "")
    
    return table


def get_config_details(name: str) -> None:
    """
    Display detailed information about a specific configuration.

    Args:
        name: Name of the configuration to display
    """
    if not config_manager.config_exists(name):
        console.print(f"[red]Configuration '{name}' not found.[/]")
        return
    
    config = config_manager.load_config(name)
    if not config:
        console.print(f"[red]Failed to load configuration '{name}'.[/]")
        return
    
    # Convert config to dict for display using our utility
    config_dict = pydantic_model_to_yaml(config)
    
    # Pretty print the configuration
    console.print(f"[bold cyan]Configuration: {name}[/]")
    console.print()
    
    yaml_str = yaml_safe_dump(config_dict, default_flow_style=False, sort_keys=False)
    console.print(yaml_str) 