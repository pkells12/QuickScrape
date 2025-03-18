"""Tests for the export utility functions."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, TYPE_CHECKING

import pytest
from unittest.mock import patch, MagicMock

from quickscrape.export.base import ExportFormat
from quickscrape.export.config import ExportConfig
from quickscrape.export.utils import export_data, export_data_to_string

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def sample_data() -> List[Dict[str, Any]]:
    """Sample data for testing exporters.
    
    Returns:
        List of dictionaries with test data
    """
    return [
        {"id": 1, "name": "Item 1", "price": 19.99, "in_stock": True},
        {"id": 2, "name": "Item 2", "price": 29.99, "in_stock": False},
    ]


class TestExportData:
    """Tests for the export_data function."""
    
    def test_export_data_with_default_config(
        self, sample_data: List[Dict[str, Any]], tmp_path: Path
    ) -> None:
        """Test exporting data with default configuration.
        
        Args:
            sample_data: Sample data fixture
            tmp_path: Pytest temporary directory
        """
        output_path = os.path.join(tmp_path, "test_output.json")
        
        with patch("quickscrape.export.utils.ExportConfig") as mock_config_class:
            # Setup mock config
            mock_config = MagicMock()
            mock_config.format = ExportFormat.JSON
            mock_config.get_output_filepath.return_value = output_path
            mock_config.get_exporter_kwargs.return_value = {"pretty": True}
            mock_config_class.return_value = mock_config
            
            # Call export_data
            result = export_data(sample_data, "test_config")
            
            # Check results
            assert result == output_path
            assert os.path.exists(output_path)
            
            # Verify file contents
            with open(output_path, "r") as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]["id"] == 1
                assert data[0]["name"] == "Item 1"
    
    def test_export_data_with_custom_config(
        self, sample_data: List[Dict[str, Any]], tmp_path: Path
    ) -> None:
        """Test exporting data with custom configuration.
        
        Args:
            sample_data: Sample data fixture
            tmp_path: Pytest temporary directory
        """
        # Create a test export config
        config = ExportConfig(
            format=ExportFormat.CSV,
            output_path=str(tmp_path),
            filename_template="test_export.{extension}",
        )
        
        # Expected output path
        expected_path = os.path.join(tmp_path, "test_export.csv")
        
        # Call export_data with custom config
        result = export_data(sample_data, "test_config", config)
        
        # Check results
        assert result == expected_path
        assert os.path.exists(expected_path)
        
        # Verify file is a CSV
        with open(expected_path, "r") as f:
            content = f.read()
            assert "id,in_stock,name,price" in content  # Headers in alphabetical order
            assert "1,True,Item 1,19.99" in content
    
    def test_export_data_with_explicit_path(
        self, sample_data: List[Dict[str, Any]], tmp_path: Path
    ) -> None:
        """Test exporting data with an explicitly provided filepath.
        
        Args:
            sample_data: Sample data fixture
            tmp_path: Pytest temporary directory
        """
        # Create explicit output path
        output_path = os.path.join(tmp_path, "explicit_output.json")
        
        # Call export_data with explicit path
        result = export_data(
            sample_data,
            "test_config",
            ExportConfig(format="json"),
            filepath=output_path
        )
        
        # Check results
        assert result == output_path
        assert os.path.exists(output_path)
        
        # Verify file contents
        with open(output_path, "r") as f:
            data = json.load(f)
            assert len(data) == 2
    
    def test_export_data_creates_directory(
        self, sample_data: List[Dict[str, Any]], tmp_path: Path
    ) -> None:
        """Test that export_data creates directories if needed.
        
        Args:
            sample_data: Sample data fixture
            tmp_path: Pytest temporary directory
        """
        # Create nested directory path that doesn't exist
        nested_dir = os.path.join(tmp_path, "new_dir", "nested")
        output_path = os.path.join(nested_dir, "output.json")
        
        # Call export_data with path in non-existent directory
        result = export_data(sample_data, "test_config", filepath=output_path)
        
        # Check results
        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.isdir(nested_dir)


class TestExportDataToString:
    """Tests for the export_data_to_string function."""
    
    def test_export_to_string_json(self, sample_data: List[Dict[str, Any]]) -> None:
        """Test exporting data to a JSON string.
        
        Args:
            sample_data: Sample data fixture
        """
        result = export_data_to_string(sample_data, "json")
        
        # Verify result is valid JSON
        data = json.loads(result)
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Item 1"
    
    def test_export_to_string_csv(self, sample_data: List[Dict[str, Any]]) -> None:
        """Test exporting data to a CSV string.
        
        Args:
            sample_data: Sample data fixture
        """
        result = export_data_to_string(sample_data, "csv")
        
        # Check for CSV format
        assert "id,in_stock,name,price" in result  # Headers in alphabetical order
        assert "1,True,Item 1,19.99" in result
    
    def test_export_to_string_with_options(self, sample_data: List[Dict[str, Any]]) -> None:
        """Test exporting data to a string with custom options.
        
        Args:
            sample_data: Sample data fixture
        """
        # JSON without pretty formatting
        result = export_data_to_string(sample_data, "json", pretty=False)
        assert "\n" not in result
        assert json.loads(result) == sample_data
        
        # CSV with custom delimiter
        result = export_data_to_string(sample_data, "csv", delimiter="|")
        assert "id|in_stock|name|price" in result
        assert "1|True|Item 1|19.99" in result 