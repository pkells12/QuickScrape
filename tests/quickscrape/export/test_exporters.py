"""Tests for the export implementations."""

import csv
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, TYPE_CHECKING

import pytest

from quickscrape.export.base import ExportFormat
from quickscrape.export.exporters import (
    CsvExporter,
    JsonExporter,
    ExcelExporter,
    create_exporter,
)

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
        {"id": 1, "name": "Item 1", "price": 19.99, "in_stock": True, "tags": ["tag1", "tag2"]},
        {"id": 2, "name": "Item 2", "price": 29.99, "in_stock": False, "tags": ["tag2", "tag3"]},
        {"id": 3, "name": "Item 3", "price": 39.99, "in_stock": True, "tags": ["tag1", "tag3"]},
    ]


class TestCsvExporter:
    """Tests for the CSV exporter."""
    
    def test_export_to_string(self, sample_data: List[Dict[str, Any]]) -> None:
        """Test exporting data to a CSV string.
        
        Args:
            sample_data: Sample data fixture
        """
        exporter = CsvExporter()
        result = exporter.export_to_string(sample_data)
        
        # Parse the CSV string to verify content
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]["id"] == "1"
        assert rows[0]["name"] == "Item 1"
        assert rows[0]["price"] == "19.99"
        assert rows[0]["in_stock"] == "True"
        assert rows[0]["tags"] == "['tag1', 'tag2']"
    
    def test_export_to_file(self, sample_data: List[Dict[str, Any]], tmp_path: Path) -> None:
        """Test exporting data to a CSV file.
        
        Args:
            sample_data: Sample data fixture
            tmp_path: Pytest temporary directory
        """
        output_file = tmp_path / "test_output.csv"
        exporter = CsvExporter()
        exporter.export_to_file(sample_data, output_file)
        
        # Verify file exists
        assert output_file.exists()
        
        # Verify content
        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3
            assert rows[0]["id"] == "1"
            assert rows[0]["name"] == "Item 1"
    
    def test_no_headers(self, sample_data: List[Dict[str, Any]]) -> None:
        """Test exporting data without headers.
        
        Args:
            sample_data: Sample data fixture
        """
        exporter = CsvExporter(include_headers=False)
        result = exporter.export_to_string(sample_data)
        
        # Split into lines and check no headers
        lines = result.strip().split("\n")
        assert len(lines) == 3  # Only data rows, no header
        
        # First line should be data, not headers
        first_line = lines[0].split(",")
        assert "id" not in first_line
        assert "1" in first_line
    
    def test_custom_delimiter(self, sample_data: List[Dict[str, Any]]) -> None:
        """Test using a custom delimiter.
        
        Args:
            sample_data: Sample data fixture
        """
        exporter = CsvExporter(delimiter="|")
        result = exporter.export_to_string(sample_data)
        
        # Check that pipe is used as delimiter
        assert "|" in result
        assert "," not in result.split("\n")[0]  # Check first line doesn't have commas


class TestJsonExporter:
    """Tests for the JSON exporter."""
    
    def test_export_to_string(self, sample_data: List[Dict[str, Any]]) -> None:
        """Test exporting data to a JSON string.
        
        Args:
            sample_data: Sample data fixture
        """
        exporter = JsonExporter()
        result = exporter.export_to_string(sample_data)
        
        # Parse JSON and verify
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0]["id"] == 1
        assert parsed[0]["name"] == "Item 1"
        assert parsed[0]["price"] == 19.99
        assert parsed[0]["in_stock"] is True
        assert parsed[0]["tags"] == ["tag1", "tag2"]
    
    def test_export_to_file(self, sample_data: List[Dict[str, Any]], tmp_path: Path) -> None:
        """Test exporting data to a JSON file.
        
        Args:
            sample_data: Sample data fixture
            tmp_path: Pytest temporary directory
        """
        output_file = tmp_path / "test_output.json"
        exporter = JsonExporter()
        exporter.export_to_file(sample_data, output_file)
        
        # Verify file exists
        assert output_file.exists()
        
        # Verify content
        with open(output_file, "r") as f:
            parsed = json.load(f)
            assert len(parsed) == 3
            assert parsed[0]["id"] == 1
            assert parsed[0]["name"] == "Item 1"
    
    def test_pretty_vs_compact(self, sample_data: List[Dict[str, Any]]) -> None:
        """Test pretty vs compact formatting.
        
        Args:
            sample_data: Sample data fixture
        """
        # Pretty format (default)
        pretty_exporter = JsonExporter(pretty=True)
        pretty_result = pretty_exporter.export_to_string(sample_data)
        
        # Compact format
        compact_exporter = JsonExporter(pretty=False)
        compact_result = compact_exporter.export_to_string(sample_data)
        
        # Pretty should have newlines, compact should not
        assert "\n" in pretty_result
        assert "\n" not in compact_result
        
        # Both should produce valid JSON with same content
        assert json.loads(pretty_result) == json.loads(compact_result)


class TestExcelExporter:
    """Tests for the Excel exporter."""
    
    def test_export_to_file(self, sample_data: List[Dict[str, Any]], tmp_path: Path) -> None:
        """Test exporting data to an Excel file.
        
        Args:
            sample_data: Sample data fixture
            tmp_path: Pytest temporary directory
        """
        try:
            import pandas as pd
            
            output_file = tmp_path / "test_output.xlsx"
            exporter = ExcelExporter()
            exporter.export_to_file(sample_data, output_file)
            
            # Verify file exists
            assert output_file.exists()
            
            # Read the Excel file and verify content
            df = pd.read_excel(output_file)
            assert len(df) == 3
            assert df.iloc[0]["id"] == 1
            assert df.iloc[0]["name"] == "Item 1"
            assert df.iloc[0]["price"] == 19.99
            assert bool(df.iloc[0]["in_stock"]) is True  # Convert to Python bool for comparison
            
        except ImportError:
            pytest.skip("pandas not installed, skipping Excel export tests")
    
    def test_custom_sheet_name(self, sample_data: List[Dict[str, Any]], tmp_path: Path) -> None:
        """Test using a custom sheet name.
        
        Args:
            sample_data: Sample data fixture
            tmp_path: Pytest temporary directory
        """
        try:
            import pandas as pd
            import openpyxl
            
            sheet_name = "TestSheet"
            output_file = tmp_path / "test_output_custom_sheet.xlsx"
            exporter = ExcelExporter(sheet_name=sheet_name)
            exporter.export_to_file(sample_data, output_file)
            
            # Verify file exists
            assert output_file.exists()
            
            # Check sheet name
            wb = openpyxl.load_workbook(output_file)
            assert sheet_name in wb.sheetnames
            
        except ImportError:
            pytest.skip("pandas or openpyxl not installed, skipping Excel sheet name test")


class TestCreateExporter:
    """Tests for the exporter factory function."""
    
    def test_create_exporter_from_enum(self) -> None:
        """Test creating exporters from format enum values."""
        assert isinstance(create_exporter(ExportFormat.CSV), CsvExporter)
        assert isinstance(create_exporter(ExportFormat.JSON), JsonExporter)
        assert isinstance(create_exporter(ExportFormat.EXCEL), ExcelExporter)
    
    def test_create_exporter_from_string(self) -> None:
        """Test creating exporters from format strings."""
        assert isinstance(create_exporter("csv"), CsvExporter)
        assert isinstance(create_exporter("json"), JsonExporter)
        assert isinstance(create_exporter("excel"), ExcelExporter)
        assert isinstance(create_exporter("xlsx"), ExcelExporter)
        
        # Case insensitive
        assert isinstance(create_exporter("CSV"), CsvExporter)
        assert isinstance(create_exporter("Json"), JsonExporter)
    
    def test_invalid_format(self) -> None:
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            create_exporter("invalid_format")
    
    def test_exporter_with_options(self) -> None:
        """Test creating exporters with custom options."""
        csv_exporter = create_exporter("csv", delimiter="|", include_headers=False)
        assert isinstance(csv_exporter, CsvExporter)
        assert csv_exporter.delimiter == "|"
        assert csv_exporter.include_headers is False
        
        excel_exporter = create_exporter("excel", sheet_name="CustomSheet")
        assert isinstance(excel_exporter, ExcelExporter)
        assert excel_exporter.sheet_name == "CustomSheet" 