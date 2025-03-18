"""Tests for the export configuration module."""

import os
from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from quickscrape.export.base import ExportFormat
from quickscrape.export.config import ExportConfig

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestExportConfig:
    """Tests for the ExportConfig class."""
    
    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        config = ExportConfig()
        
        # Check default values
        assert config.format == ExportFormat.JSON
        assert config.output_path == "./output"
        assert config.filename_template == "{config_name}_{timestamp}.{extension}"
        assert config.pretty is True
        assert config.encoding == "utf-8"
        assert config.csv_delimiter == ","
        assert config.include_headers is True
        assert config.excel_sheet_name == "Data"
    
    def test_custom_values(self) -> None:
        """Test initialization with custom values."""
        config = ExportConfig(
            format="csv",
            output_path="/custom/path",
            filename_template="export_{date}.{extension}",
            pretty=False,
            encoding="latin-1",
            csv_delimiter="|",
            include_headers=False,
            excel_sheet_name="CustomSheet",
        )
        
        # Check custom values
        assert config.format == ExportFormat.CSV
        assert config.output_path == "/custom/path"
        assert config.filename_template == "export_{date}.{extension}"
        assert config.pretty is False
        assert config.encoding == "latin-1"
        assert config.csv_delimiter == "|"
        assert config.include_headers is False
        assert config.excel_sheet_name == "CustomSheet"
    
    def test_format_validation(self) -> None:
        """Test format validation."""
        # Valid formats
        assert ExportConfig(format="csv").format == ExportFormat.CSV
        assert ExportConfig(format="json").format == ExportFormat.JSON
        assert ExportConfig(format="excel").format == ExportFormat.EXCEL
        assert ExportConfig(format=ExportFormat.CSV).format == ExportFormat.CSV
        
        # Invalid format
        with pytest.raises(ValidationError):
            ExportConfig(format="invalid")
    
    def test_get_output_filepath(self, monkeypatch: "MonkeyPatch") -> None:
        """Test generating output filepath.
        
        Args:
            monkeypatch: Pytest monkeypatch fixture
        """
        # Freeze datetime for consistent testing
        frozen_datetime = datetime(2021, 1, 1, 12, 0, 0)
        monkeypatch.setattr(
            "quickscrape.export.config.datetime",
            type("MockDatetime", (), {
                "now": lambda: frozen_datetime
            })
        )
        
        config = ExportConfig(
            output_path="/test/output",
            filename_template="{config_name}_{date}_{time}.{extension}"
        )
        
        filepath = config.get_output_filepath("test_config")
        expected = "/test/output/test_config_2021-01-01_12-00-00.json"
        assert filepath == expected
        
        # Test with different format
        config.format = ExportFormat.CSV
        filepath = config.get_output_filepath("test_config")
        expected = "/test/output/test_config_2021-01-01_12-00-00.csv"
        assert filepath == expected
    
    def test_get_exporter_kwargs(self) -> None:
        """Test getting format-specific exporter parameters."""
        # Test JSON format
        json_config = ExportConfig(format="json", pretty=False, encoding="latin-1")
        json_kwargs = json_config.get_exporter_kwargs()
        assert json_kwargs == {"pretty": False, "encoding": "latin-1"}
        
        # Test CSV format
        csv_config = ExportConfig(
            format="csv",
            pretty=True,
            encoding="utf-8",
            csv_delimiter="|",
            include_headers=False
        )
        csv_kwargs = csv_config.get_exporter_kwargs()
        assert csv_kwargs == {
            "pretty": True,
            "encoding": "utf-8",
            "delimiter": "|",
            "include_headers": False
        }
        
        # Test Excel format
        excel_config = ExportConfig(
            format="excel",
            pretty=True,
            encoding="utf-8",
            excel_sheet_name="TestSheet",
            include_headers=True
        )
        excel_kwargs = excel_config.get_exporter_kwargs()
        assert excel_kwargs == {
            "pretty": True,
            "encoding": "utf-8",
            "sheet_name": "TestSheet",
            "include_headers": True
        } 