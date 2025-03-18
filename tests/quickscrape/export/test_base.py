"""Tests for the base export module."""

import pytest
from typing import TYPE_CHECKING

from quickscrape.export.base import ExportFormat

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestExportFormat:
    """Tests for the ExportFormat enum."""
    
    def test_from_string_valid_formats(self) -> None:
        """Test valid string conversion to ExportFormat enum."""
        # Test all valid format strings
        assert ExportFormat.from_string("csv") == ExportFormat.CSV
        assert ExportFormat.from_string("json") == ExportFormat.JSON
        assert ExportFormat.from_string("excel") == ExportFormat.EXCEL
        assert ExportFormat.from_string("xlsx") == ExportFormat.EXCEL
        assert ExportFormat.from_string("xls") == ExportFormat.EXCEL
        
        # Test case insensitivity
        assert ExportFormat.from_string("CSV") == ExportFormat.CSV
        assert ExportFormat.from_string("Json") == ExportFormat.JSON
        assert ExportFormat.from_string("EXCEL") == ExportFormat.EXCEL
    
    def test_from_string_invalid_format(self) -> None:
        """Test that invalid format strings raise ValueError."""
        with pytest.raises(ValueError):
            ExportFormat.from_string("invalid_format")
        
        with pytest.raises(ValueError):
            ExportFormat.from_string("txt")
    
    def test_file_extension(self) -> None:
        """Test file extension property."""
        assert ExportFormat.CSV.file_extension == "csv"
        assert ExportFormat.JSON.file_extension == "json"
        assert ExportFormat.EXCEL.file_extension == "xlsx" 