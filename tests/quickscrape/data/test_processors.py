"""Tests for the data processors module."""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import pytest

from quickscrape.data.processors import (
    ProcessorType,
    ProcessorConfig,
    StringProcessor,
    NumberProcessor,
    DateProcessor,
    BooleanProcessor,
    ListProcessor,
    CustomProcessor,
    DataProcessor,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestStringProcessor:
    """Tests for the string processor."""

    def test_basic_string_conversion(self) -> None:
        """Test basic string conversion."""
        config: ProcessorConfig = {
            "type": ProcessorType.STRING
        }
        processor = StringProcessor(config)
        
        assert processor.process("test") == "test"
        assert processor.process(123) == "123"
        assert processor.process(None) is None

    def test_string_strip(self) -> None:
        """Test string stripping."""
        config: ProcessorConfig = {
            "type": ProcessorType.STRING,
            "strip": True
        }
        processor = StringProcessor(config)
        
        assert processor.process("  test  ") == "test"
        assert processor.process(" \t\n test \t\n ") == "test"

    def test_string_null_values(self) -> None:
        """Test conversion of null-like strings to None."""
        config: ProcessorConfig = {
            "type": ProcessorType.STRING,
            "to_null_values": ["N/A", "none", ""]
        }
        processor = StringProcessor(config)
        
        assert processor.process("N/A") is None
        assert processor.process("none") is None
        assert processor.process("") is None
        assert processor.process("test") == "test"

    def test_string_replacements(self) -> None:
        """Test string replacements."""
        config: ProcessorConfig = {
            "type": ProcessorType.STRING,
            "replace_map": {
                "old": "new",
                "bad": "good"
            }
        }
        processor = StringProcessor(config)
        
        assert processor.process("old text") == "new text"
        assert processor.process("bad text") == "good text"
        assert processor.process("old bad text") == "new good text"

    def test_string_pattern_validation(self) -> None:
        """Test string pattern validation."""
        config: ProcessorConfig = {
            "type": ProcessorType.STRING,
            "pattern": r"^[A-Z]\d+$",
            "default": "INVALID"
        }
        processor = StringProcessor(config)
        
        assert processor.process("A123") == "A123"
        assert processor.process("B456") == "B456"
        assert processor.process("invalid") == "INVALID"
        assert processor.process("123") == "INVALID"

    def test_string_allowed_values(self) -> None:
        """Test allowed values validation."""
        config: ProcessorConfig = {
            "type": ProcessorType.STRING,
            "allowed_values": ["red", "green", "blue"],
            "default": "unknown"
        }
        processor = StringProcessor(config)
        
        assert processor.process("red") == "red"
        assert processor.process("green") == "green"
        assert processor.process("yellow") == "unknown"


class TestNumberProcessor:
    """Tests for the number processor."""

    def test_basic_number_conversion(self) -> None:
        """Test basic number conversion."""
        config: ProcessorConfig = {
            "type": ProcessorType.NUMBER
        }
        processor = NumberProcessor(config)
        
        assert processor.process(123) == 123
        assert processor.process("123") == 123.0
        assert processor.process("123.45") == 123.45
        assert processor.process(None) is None

    def test_integer_conversion(self) -> None:
        """Test integer conversion."""
        config: ProcessorConfig = {
            "type": ProcessorType.NUMBER,
            "format": "integer"
        }
        processor = NumberProcessor(config)
        
        assert processor.process(123) == 123
        assert processor.process("123") == 123
        assert processor.process("123.45") == 123
        assert processor.process(123.45) == 123

    def test_number_min_max_validation(self) -> None:
        """Test number min/max validation."""
        config: ProcessorConfig = {
            "type": ProcessorType.NUMBER,
            "min_value": 10,
            "max_value": 100,
            "default": 50
        }
        processor = NumberProcessor(config)
        
        assert processor.process(50) == 50
        assert processor.process(10) == 10
        assert processor.process(100) == 100
        assert processor.process(5) == 50
        assert processor.process(150) == 50

    def test_number_cleaning(self) -> None:
        """Test cleaning of non-numeric characters."""
        config: ProcessorConfig = {
            "type": ProcessorType.NUMBER
        }
        processor = NumberProcessor(config)
        
        assert processor.process("$123.45") == 123.45
        assert processor.process("123,456.78") == 123456.78
        assert processor.process("Price: $99.99") == 99.99


class TestDateProcessor:
    """Tests for the date processor."""

    def test_basic_date_conversion(self) -> None:
        """Test basic date conversion with the default format."""
        config: ProcessorConfig = {
            "type": ProcessorType.DATE
        }
        processor = DateProcessor(config)
        
        result = processor.process("2021-05-15")
        assert isinstance(result, datetime)
        assert result.year == 2021
        assert result.month == 5
        assert result.day == 15

    def test_custom_format_date_conversion(self) -> None:
        """Test date conversion with a custom format."""
        config: ProcessorConfig = {
            "type": ProcessorType.DATE,
            "format": "%d/%m/%Y"
        }
        processor = DateProcessor(config)
        
        result = processor.process("15/05/2021")
        assert isinstance(result, datetime)
        assert result.year == 2021
        assert result.month == 5
        assert result.day == 15

    def test_automatic_format_detection(self) -> None:
        """Test automatic format detection for common date formats."""
        config: ProcessorConfig = {
            "type": ProcessorType.DATE
        }
        processor = DateProcessor(config)
        
        # Test various formats
        formats_and_dates = [
            ("15/05/2021", 15, 5, 2021),
            ("05/15/2021", 15, 5, 2021),
            ("2021/05/15", 15, 5, 2021),
            ("15-05-2021", 15, 5, 2021),
            ("2021-05-15T12:30:45", 15, 5, 2021),
        ]
        
        for date_str, day, month, year in formats_and_dates:
            result = processor.process(date_str)
            assert isinstance(result, datetime)
            assert result.day == day
            assert result.month == month
            assert result.year == year

    def test_invalid_date(self) -> None:
        """Test handling of invalid dates."""
        config: ProcessorConfig = {
            "type": ProcessorType.DATE,
            "default": datetime(2000, 1, 1)
        }
        processor = DateProcessor(config)
        
        result = processor.process("not a date")
        assert result == datetime(2000, 1, 1)


class TestBooleanProcessor:
    """Tests for the boolean processor."""

    def test_basic_boolean_conversion(self) -> None:
        """Test basic boolean conversion."""
        config: ProcessorConfig = {
            "type": ProcessorType.BOOLEAN
        }
        processor = BooleanProcessor(config)
        
        assert processor.process(True) is True
        assert processor.process(False) is False
        assert processor.process(1) is True
        assert processor.process(0) is False
        assert processor.process(None) is None

    def test_string_boolean_conversion(self) -> None:
        """Test conversion of string representations of booleans."""
        config: ProcessorConfig = {
            "type": ProcessorType.BOOLEAN
        }
        processor = BooleanProcessor(config)
        
        true_values = ["true", "yes", "y", "1", "t", "True", "YES"]
        false_values = ["false", "no", "n", "0", "f", "False", "NO"]
        
        for value in true_values:
            assert processor.process(value) is True
        
        for value in false_values:
            assert processor.process(value) is False
        
        # Other strings should convert to None
        assert processor.process("maybe") is None
        assert processor.process("unknown") is None


class TestListProcessor:
    """Tests for the list processor."""

    def test_basic_list_handling(self) -> None:
        """Test basic list handling."""
        config: ProcessorConfig = {
            "type": ProcessorType.LIST
        }
        processor = ListProcessor(config)
        
        # Already a list
        result = processor.process(["a", "b", "c"])
        assert result == ["a", "b", "c"]
        
        # String to split
        result = processor.process("a,b,c")
        assert result == ["a", "b", "c"]
        
        # Single value to wrap
        result = processor.process("single")
        assert result == ["single"]

    def test_custom_separator(self) -> None:
        """Test list processing with a custom separator."""
        config: ProcessorConfig = {
            "type": ProcessorType.LIST,
            "list_separator": "|"
        }
        processor = ListProcessor(config)
        
        result = processor.process("a|b|c")
        assert result == ["a", "b", "c"]

    def test_item_processor(self) -> None:
        """Test list with item processor configuration."""
        config: ProcessorConfig = {
            "type": ProcessorType.LIST,
            "list_item_processor": {
                "type": ProcessorType.NUMBER,
                "format": "integer"
            }
        }
        processor = ListProcessor(config)
        
        result = processor.process("1,2,3")
        assert result == [1, 2, 3]
        
        result = processor.process(["1.5", "2.7", "3.9"])
        assert result == [1, 2, 3]


class TestCustomProcessor:
    """Tests for the custom processor."""

    def test_capitalize_function(self) -> None:
        """Test the capitalize function."""
        config: ProcessorConfig = {
            "type": ProcessorType.CUSTOM,
            "custom_function": "capitalize"
        }
        processor = CustomProcessor(config)
        
        assert processor.process("test") == "Test"
        assert processor.process("ALREADY CAPS") == "Already caps"
        assert processor.process(None) is None

    def test_title_case_function(self) -> None:
        """Test the title_case function."""
        config: ProcessorConfig = {
            "type": ProcessorType.CUSTOM,
            "custom_function": "title_case"
        }
        processor = CustomProcessor(config)
        
        assert processor.process("hello world") == "Hello World"
        assert processor.process("THIS IS A TEST") == "This Is A Test"

    def test_remove_html_function(self) -> None:
        """Test the remove_html function."""
        config: ProcessorConfig = {
            "type": ProcessorType.CUSTOM,
            "custom_function": "remove_html"
        }
        processor = CustomProcessor(config)
        
        assert processor.process("<p>Test</p>") == "Test"
        assert processor.process("<a href='#'>Link <b>text</b></a>") == "Link text"

    def test_extract_digits_function(self) -> None:
        """Test the extract_digits function."""
        config: ProcessorConfig = {
            "type": ProcessorType.CUSTOM,
            "custom_function": "extract_digits"
        }
        processor = CustomProcessor(config)
        
        assert processor.process("abc123def") == "123"
        assert processor.process("Price: $99.99") == "9999"
        assert processor.process("No digits") == ""

    def test_normalize_whitespace_function(self) -> None:
        """Test the normalize_whitespace function."""
        config: ProcessorConfig = {
            "type": ProcessorType.CUSTOM,
            "custom_function": "normalize_whitespace"
        }
        processor = CustomProcessor(config)
        
        assert processor.process("  Multiple    spaces  ") == "Multiple spaces"
        assert processor.process("Line\nbreaks\tand\ttabs") == "Line breaks and tabs"


class TestDataProcessor:
    """Tests for the main DataProcessor class."""

    def test_process_multiple_fields(self) -> None:
        """Test processing of multiple fields at once."""
        processing_config: Dict[str, ProcessorConfig] = {
            "name": {
                "type": ProcessorType.STRING,
                "transform": "strip"
            },
            "age": {
                "type": ProcessorType.NUMBER,
                "format": "integer",
                "min_value": 0,
                "max_value": 150
            },
            "is_active": {
                "type": ProcessorType.BOOLEAN
            }
        }
        
        processor = DataProcessor(processing_config)
        
        input_data = {
            "name": " John Doe ",
            "age": "35",
            "is_active": "yes",
            "extra_field": "extra value"
        }
        
        result = processor.process(input_data)
        
        assert result["name"] == "John Doe"
        assert result["age"] == 35
        assert result["is_active"] is True
        assert result["extra_field"] == "extra value"

    def test_default_values(self) -> None:
        """Test application of default values for missing fields."""
        processing_config: Dict[str, ProcessorConfig] = {
            "name": {
                "type": ProcessorType.STRING,
                "default": "Unknown"
            },
            "age": {
                "type": ProcessorType.NUMBER,
                "default": 0
            }
        }
        
        processor = DataProcessor(processing_config)
        
        # Missing fields
        input_data = {
            "other_field": "value"
        }
        
        result = processor.process(input_data)
        
        assert result["name"] == "Unknown"
        assert result["age"] == 0
        assert result["other_field"] == "value"

    def test_validation_and_defaults(self) -> None:
        """Test validation with defaults for invalid values."""
        processing_config: Dict[str, ProcessorConfig] = {
            "email": {
                "type": ProcessorType.STRING,
                "pattern": r"^[^@]+@[^@]+\.[^@]+$",
                "default": "invalid@example.com"
            },
            "score": {
                "type": ProcessorType.NUMBER,
                "min_value": 0,
                "max_value": 100,
                "default": 50
            }
        }
        
        processor = DataProcessor(processing_config)
        
        input_data = {
            "email": "not-an-email",
            "score": 150
        }
        
        result = processor.process(input_data)
        
        assert result["email"] == "invalid@example.com"
        assert result["score"] == 50

    def test_complex_processing_chain(self) -> None:
        """Test a more complex processing chain with multiple processor types."""
        processing_config: Dict[str, ProcessorConfig] = {
            "title": {
                "type": ProcessorType.CUSTOM,
                "custom_function": "title_case"
            },
            "prices": {
                "type": ProcessorType.LIST,
                "list_item_processor": {
                    "type": ProcessorType.NUMBER
                }
            },
            "description": {
                "type": ProcessorType.CUSTOM,
                "custom_function": "remove_html"
            },
            "created_at": {
                "type": ProcessorType.DATE,
                "format": "%Y-%m-%d"
            }
        }
        
        processor = DataProcessor(processing_config)
        
        input_data = {
            "title": "PRODUCT NAME",
            "prices": "$10.99, $12.99, $15.99",
            "description": "<p>This is a <b>product</b> description.</p>",
            "created_at": "2021-05-15"
        }
        
        result = processor.process(input_data)
        
        assert result["title"] == "Product Name"
        assert result["prices"] == [10.99, 12.99, 15.99]
        assert result["description"] == "This is a product description."
        assert isinstance(result["created_at"], datetime)
        assert result["created_at"].year == 2021
        assert result["created_at"].month == 5
        assert result["created_at"].day == 15 