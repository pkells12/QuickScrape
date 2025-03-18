"""
Unit tests for the initialization utilities.

This module contains tests for the configuration initialization functionality.
"""

from pathlib import Path
from typing import Generator

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from quickscrape.config import config_manager
from quickscrape.config.init import initialize_config, create_example_configs


@pytest.fixture
def mock_config_dir(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """
    Mock the configuration directory to use a temporary directory.

    Args:
        monkeypatch: pytest monkeypatch fixture
        tmp_path: temporary directory path from pytest

    Returns:
        Path: The path to the mocked configuration directory
    """
    # Mock the get_config_dir function to return our temporary directory
    monkeypatch.setattr(
        config_manager, "get_config_dir", lambda: tmp_path
    )
    
    # Also set the environment variable
    monkeypatch.setenv("QUICKSCRAPE_CONFIG_DIR", str(tmp_path))
    
    return tmp_path


def test_initialize_config(mock_config_dir: Path, capsys: CaptureFixture) -> None:
    """
    Test initializing a new configuration.

    Args:
        mock_config_dir: mocked configuration directory
        capsys: pytest fixture for capturing stdout/stderr
    """
    # Initialize a new configuration
    result = initialize_config("test_init")
    
    # Check the result
    assert result is True
    
    # Check that the configuration file was created
    config_path = mock_config_dir / "test_init.yaml"
    assert config_path.exists()
    
    # Check the console output
    captured = capsys.readouterr()
    assert "Configuration 'test_init' initialized successfully!" in captured.out


def test_initialize_config_force(mock_config_dir: Path, capsys: CaptureFixture) -> None:
    """
    Test overwriting an existing configuration with force=True.

    Args:
        mock_config_dir: mocked configuration directory
        capsys: pytest fixture for capturing stdout/stderr
    """
    # Create an initial configuration
    config_path = mock_config_dir / "test_force.yaml"
    with open(config_path, "w") as f:
        f.write("url: https://example.com/original")
    
    # Try to initialize without force (should fail)
    result = initialize_config("test_force", force=False)
    assert result is False
    
    # Check the console output
    captured = capsys.readouterr()
    assert "Configuration 'test_force' already exists" in captured.out
    
    # Try to initialize with force (should succeed)
    result = initialize_config("test_force", force=True)
    assert result is True
    
    # Check the console output
    captured = capsys.readouterr()
    assert "Configuration 'test_force' initialized successfully!" in captured.out


def test_create_example_configs(mock_config_dir: Path, capsys: CaptureFixture) -> None:
    """
    Test creating example configurations.

    Args:
        mock_config_dir: mocked configuration directory
        capsys: pytest fixture for capturing stdout/stderr
    """
    # Create example configurations
    create_example_configs()
    
    # Check that the examples directory was created
    examples_dir = mock_config_dir / "examples"
    assert examples_dir.exists()
    
    # Check that the example files were created
    assert (examples_dir / "product_scraper.yaml").exists()
    assert (examples_dir / "news_scraper.yaml").exists()
    assert (examples_dir / "simple_list.yaml").exists()
    
    # Check the console output
    captured = capsys.readouterr()
    assert "Created 3 example configurations" in captured.out 