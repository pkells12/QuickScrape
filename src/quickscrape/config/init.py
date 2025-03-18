"""
Initialization utilities for QuickScrape.

This module handles the initialization of new scraping configurations.
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel

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
from quickscrape.utils.yaml_utils import pydantic_model_to_yaml, yaml_safe_dump

logger = get_logger(__name__)
console = Console()


def initialize_config(name: str, force: bool = False) -> bool:
    """
    Initialize a new scraping configuration.

    Creates a new configuration file with default settings that can be
    customized for a specific scraping task.

    Args:
        name: Name for the new configuration
        force: Whether to overwrite an existing configuration with the same name

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    if config_manager.config_exists(name) and not force:
        console.print(
            Panel(
                f"[bold red]Configuration '{name}' already exists.[/]\n\n"
                f"Use [bold]--force[/] to overwrite it, or choose a different name.",
                title="Configuration Exists",
                border_style="red",
            )
        )
        return False

    # Get the default configuration
    config = config_manager.get_default_config()
    
    # Save it with the given name
    success = config_manager.save_config(config, name, force)
    
    if success:
        config_path = config_manager.get_config_path(name)
        console.print(
            Panel(
                f"[bold green]Configuration '{name}' initialized successfully![/]\n\n"
                f"Configuration saved to: [bold]{config_path}[/]\n\n"
                f"Edit this file to customize your scraping configuration, or use the "
                f"[bold]wizard[/] command to set it up interactively.",
                title="Configuration Initialized",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]Failed to initialize configuration '{name}'.[/]\n\n"
                f"Check the logs for more information.",
                title="Initialization Failed",
                border_style="red",
            )
        )
    
    return success


def create_example_configs() -> None:
    """
    Create example configurations in the samples directory.
    
    This function creates several example configurations demonstrating
    different scraping scenarios.
    """
    examples = {
        "product_scraper": ScraperConfig(
            url="https://example.com/products",
            selectors={
                "product_name": ".product-title",
                "product_price": ".product-price",
                "product_description": ".product-description",
                "product_rating": ".product-rating",
            },
            wait_time=1.0,
            pagination=PaginationConfig(
                type=PaginationType.NEXT_BUTTON,
                selector=".pagination .next",
                max_pages=5,
            ),
            output=OutputConfig(
                format=OutputFormat.CSV,
                path="products.csv",
            ),
        ),
        
        "news_scraper": ScraperConfig(
            url="https://example.com/news",
            selectors={
                "headline": "h2.headline",
                "date": ".article-date",
                "author": ".author-name",
                "summary": ".article-summary",
                "content": ".article-content p",
            },
            wait_time=2.0,
            pagination=PaginationConfig(
                type=PaginationType.URL_PARAM,
                param_name="page",
                max_pages=10,
            ),
            output=OutputConfig(
                format=OutputFormat.JSON,
                path="news_articles.json",
            ),
        ),
        
        "simple_list": ScraperConfig(
            url="https://example.com/list",
            selectors={
                "item_name": ".list-item .name",
                "item_value": ".list-item .value",
            },
            output=OutputConfig(
                format=OutputFormat.CSV,
                path="list_items.csv",
            ),
        ),
    }
    
    # Create the examples directory
    import os
    from pathlib import Path
    
    examples_dir = Path(config_manager.get_config_dir()) / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    # Save each example
    success_count = 0
    for name, config in examples.items():
        # We'll use a custom path to save in the examples subdirectory
        config_path = examples_dir / f"{name}.yaml"
        
        try:
            # Convert Pydantic model to dict with proper handling of enums
            config_dict = pydantic_model_to_yaml(config)
            
            # Save to YAML file using our custom dumper
            with open(config_path, "w") as file:
                yaml_safe_dump(config_dict, file, default_flow_style=False, sort_keys=False)
            
            success_count += 1
            logger.info(f"Created example configuration: {config_path}")
        except Exception as e:
            logger.error(f"Failed to create example {name}: {e}")
    
    if success_count > 0:
        console.print(
            f"[green]Created {success_count} example configurations in "
            f"{examples_dir}[/]"
        ) 