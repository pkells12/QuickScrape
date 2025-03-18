"""
Configuration management for QuickScrape.

This module provides functions for loading, saving, and validating
QuickScrape configuration files.
"""

import os
import pathlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, ValidationError

from quickscrape.config.models import ScraperConfig
from quickscrape.utils.logger import get_logger
from quickscrape.utils.yaml_utils import pydantic_model_to_yaml, yaml_safe_dump, yaml_safe_load

logger = get_logger(__name__)


def get_config_dir() -> Path:
    """
    Get the QuickScrape configuration directory.

    The directory is determined in the following order:
    1. Custom path set in QUICKSCRAPE_CONFIG_DIR environment variable
    2. Default path at ~/.quickscrape

    Returns:
        Path: Path to the configuration directory
    """
    config_dir = os.environ.get("QUICKSCRAPE_CONFIG_DIR")
    if config_dir:
        path = Path(config_dir)
    else:
        path = Path.home() / ".quickscrape"

    # Create the directory if it doesn't exist
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created configuration directory at: {path}")

    return path


def get_config_path(name: str) -> Path:
    """
    Get the path to a specific configuration file.

    Args:
        name: Name of the configuration file (without extension)

    Returns:
        Path: Path to the configuration file
    """
    config_dir = get_config_dir()
    # Ensure the name doesn't include a file extension
    base_name = os.path.splitext(name)[0]
    return config_dir / f"{base_name}.yaml"


def list_configs() -> List[str]:
    """
    List all available configuration files.

    Returns:
        List[str]: List of configuration names (without extensions)
    """
    config_dir = get_config_dir()
    if not config_dir.exists():
        return []

    # Find all YAML files in the config directory
    yaml_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))
    
    # Extract just the base names without extensions
    return [file.stem for file in yaml_files]


def config_exists(name: str) -> bool:
    """
    Check if a configuration with the given name exists.

    Args:
        name: Name of the configuration to check

    Returns:
        bool: True if the configuration exists, False otherwise
    """
    return get_config_path(name).exists()


def load_config(name: str) -> Optional[ScraperConfig]:
    """
    Load a configuration from a file.

    Args:
        name: Name of the configuration to load

    Returns:
        Optional[ScraperConfig]: The loaded configuration, or None if it doesn't exist
                            or is invalid
    """
    config_path = get_config_path(name)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        return None

    try:
        with open(config_path, "r") as file:
            config_data = yaml_safe_load(file)
        
        # Validate using Pydantic model
        config = ScraperConfig(**config_data)
        logger.info(f"Successfully loaded configuration: {name}")
        return config
    
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML in {config_path}: {e}")
        return None
    
    except ValidationError as e:
        logger.error(f"Invalid configuration in {config_path}: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error loading {config_path}: {e}")
        return None


def save_config(config: ScraperConfig, name: str, force: bool = False) -> bool:
    """
    Save a configuration to a file.

    Args:
        config: Configuration to save
        name: Name to save the configuration as
        force: Whether to overwrite an existing configuration

    Returns:
        bool: True if the configuration was saved successfully, False otherwise
    """
    config_path = get_config_path(name)
    
    # Check if the configuration already exists
    if config_path.exists() and not force:
        logger.error(f"Configuration already exists: {config_path}. Use force=True to overwrite.")
        return False
    
    try:
        # Convert Pydantic model to dict with proper handling of enums
        config_dict = pydantic_model_to_yaml(config)
        
        # Save to YAML file using our custom dumper
        with open(config_path, "w") as file:
            yaml_safe_dump(config_dict, file, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully saved configuration to: {config_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
        return False


def get_default_config() -> ScraperConfig:
    """
    Create a default scraper configuration.

    Returns:
        ScraperConfig: A default configuration with basic settings
    """
    # Return a basic default configuration
    return ScraperConfig(
        url="https://example.com",
        selectors={
            "title": "h1",
            "content": "article p",
        },
        output={
            "format": "csv",
            "path": "output.csv",
        }
    ) 