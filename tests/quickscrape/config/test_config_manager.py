"""
Unit tests for the configuration manager.

This module contains tests for the configuration management functionality
of QuickScrape.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest
import yaml
from _pytest.monkeypatch import MonkeyPatch

from quickscrape.config import config_manager
from quickscrape.config.models import OutputConfig, OutputFormat, ScraperConfig


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for configuration files.

    Returns:
        Generator: Yields the path to the temporary directory
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config_dir(monkeypatch: MonkeyPatch, temp_config_dir: Path) -> Path:
    """
    Mock the configuration directory to use a temporary directory.

    Args:
        monkeypatch: pytest monkeypatch fixture
        temp_config_dir: temporary directory path

    Returns:
        Path: The path to the mocked configuration directory
    """
    # Mock the get_config_dir function to return our temporary directory
    monkeypatch.setattr(
        config_manager, "get_config_dir", lambda: temp_config_dir
    )
    
    # Also set the environment variable
    monkeypatch.setenv("QUICKSCRAPE_CONFIG_DIR", str(temp_config_dir))
    
    return temp_config_dir


@pytest.fixture
def sample_config() -> ScraperConfig:
    """
    Create a sample configuration for testing.

    Returns:
        ScraperConfig: A sample configuration
    """
    return ScraperConfig(
        url="https://example.com/test",
        selectors={
            "title": "h1",
            "content": ".content",
        },
        output=OutputConfig(
            format=OutputFormat.CSV,
            path="test_output.csv",
        ),
    )


def test_get_config_dir(monkeypatch: MonkeyPatch) -> None:
    """
    Test that get_config_dir returns the correct directory.
    
    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    # Test when environment variable is set
    test_dir = "/tmp/test_quickscrape_config"
    monkeypatch.setenv("QUICKSCRAPE_CONFIG_DIR", test_dir)
    assert str(config_manager.get_config_dir()) == test_dir
    
    # Test default behavior
    monkeypatch.delenv("QUICKSCRAPE_CONFIG_DIR")
    assert config_manager.get_config_dir() == Path.home() / ".quickscrape"


def test_get_config_path() -> None:
    """Test that get_config_path returns the correct path."""
    config_dir = config_manager.get_config_dir()
    
    # Test with simple name
    assert config_manager.get_config_path("test") == config_dir / "test.yaml"
    
    # Test with name that already has an extension
    assert config_manager.get_config_path("test.yml") == config_dir / "test.yaml"


def test_config_exists(mock_config_dir: Path) -> None:
    """
    Test that config_exists returns the correct result.
    
    Args:
        mock_config_dir: mocked configuration directory
    """
    # Create a test configuration file
    test_file = mock_config_dir / "exists.yaml"
    test_file.touch()
    
    assert config_manager.config_exists("exists") is True
    assert config_manager.config_exists("doesnotexist") is False


def test_list_configs(mock_config_dir: Path) -> None:
    """
    Test that list_configs returns the correct list of configurations.
    
    Args:
        mock_config_dir: mocked configuration directory
    """
    # Create some test configuration files
    (mock_config_dir / "config1.yaml").touch()
    (mock_config_dir / "config2.yml").touch()
    (mock_config_dir / "not_a_config.txt").touch()
    
    configs = config_manager.list_configs()
    assert sorted(configs) == ["config1", "config2"]


def test_save_and_load_config(mock_config_dir: Path, sample_config: ScraperConfig) -> None:
    """
    Test saving and loading a configuration.
    
    Args:
        mock_config_dir: mocked configuration directory
        sample_config: sample configuration
    """
    # Test saving
    assert config_manager.save_config(sample_config, "test_config") is True
    
    # Verify the file was created
    config_path = mock_config_dir / "test_config.yaml"
    assert config_path.exists()
    
    # Test loading
    loaded_config = config_manager.load_config("test_config")
    assert loaded_config is not None
    assert loaded_config.url == sample_config.url
    assert loaded_config.selectors == sample_config.selectors
    assert loaded_config.output.format == sample_config.output.format
    assert loaded_config.output.path == sample_config.output.path


def test_save_config_with_force(mock_config_dir: Path, sample_config: ScraperConfig) -> None:
    """
    Test that save_config with force=True overwrites existing configurations.
    
    Args:
        mock_config_dir: mocked configuration directory
        sample_config: sample configuration
    """
    # Create an initial config
    config_path = mock_config_dir / "test_config.yaml"
    with open(config_path, "w") as f:
        f.write("url: https://example.com/original")
    
    # Try to save without force (should fail)
    assert config_manager.save_config(sample_config, "test_config") is False
    
    # Try to save with force (should succeed)
    assert config_manager.save_config(sample_config, "test_config", force=True) is True
    
    # Verify the file was overwritten
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    assert data["url"] == sample_config.url


def test_load_invalid_config(mock_config_dir: Path) -> None:
    """
    Test loading an invalid configuration.
    
    Args:
        mock_config_dir: mocked configuration directory
    """
    # Create an invalid YAML file
    invalid_path = mock_config_dir / "invalid.yaml"
    with open(invalid_path, "w") as f:
        f.write("this is not valid yaml: :")
    
    # Try to load it
    assert config_manager.load_config("invalid") is None


def test_get_default_config() -> None:
    """Test that get_default_config returns a valid configuration."""
    config = config_manager.get_default_config()
    assert config is not None
    assert config.url == "https://example.com"
    assert "title" in config.selectors
    assert "content" in config.selectors
    assert config.output.format.value == "csv"
    assert config.output.path == "output.csv" 