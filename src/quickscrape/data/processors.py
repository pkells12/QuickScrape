"""Data processing module for QuickScrape.

This module provides functionality for cleaning and converting extracted data.
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Pattern, Union, TypedDict


class ProcessorType(Enum):
    """Enum defining types of data processors."""
    STRING = auto()
    NUMBER = auto()
    DATE = auto()
    BOOLEAN = auto()
    LIST = auto()
    CUSTOM = auto()


class ProcessorConfig(TypedDict, total=False):
    """Configuration options for data processors."""
    type: ProcessorType
    format: Optional[str]
    default: Any
    required: bool
    min_value: Optional[Union[int, float]]
    max_value: Optional[Union[int, float]]
    allowed_values: Optional[List[Any]]
    pattern: Optional[str]
    custom_function: Optional[str]
    strip: bool
    replace_map: Optional[Dict[str, str]]
    to_null_values: Optional[List[str]]
    list_separator: Optional[str]
    list_item_processor: Optional[Dict[str, Any]]


class BaseProcessor(ABC):
    """Base class for data processors.
    
    Implements common functionality for all processor types.
    """
    
    def __init__(self, config: ProcessorConfig) -> None:
        """Initialize the base processor.
        
        Args:
            config: Configuration dictionary for the processor
        """
        self.config = config
        self.default = config.get("default")
        self.required = config.get("required", False)
        self.strip = config.get("strip", True)
        
        # Values to convert to None
        self.to_null_values = config.get("to_null_values", ["", "null", "none", "n/a", "na"])
        
        # Replacement mappings
        self.replace_map = config.get("replace_map", {})
        
        # Validation
        self.pattern: Optional[Pattern] = None
        if pattern_str := config.get("pattern"):
            self.pattern = re.compile(pattern_str)
        
        self.allowed_values = config.get("allowed_values")
        self.min_value = config.get("min_value")
        self.max_value = config.get("max_value")
    
    def _preprocess(self, value: Any) -> Any:
        """Apply common preprocessing steps to the input value.
        
        Args:
            value: The value to preprocess
            
        Returns:
            The preprocessed value
        """
        # Convert to None if in null values list
        if isinstance(value, str):
            if self.strip:
                value = value.strip()
            
            normalized_value = value.lower()
            if normalized_value in (v.lower() for v in self.to_null_values):
                return None
            
            # Apply replacements
            for old, new in self.replace_map.items():
                value = value.replace(old, new)
        
        return value
    
    def _validate(self, value: Any) -> bool:
        """Validate the value against constraints.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is valid, False otherwise
        """
        if value is None:
            return not self.required
        
        # Check against allowed values if specified
        if self.allowed_values is not None and value not in self.allowed_values:
            return False
        
        # Check min/max for numeric values
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        
        # Check pattern for string values
        if isinstance(value, str) and self.pattern and not self.pattern.match(value):
            return False
        
        return True
    
    def process(self, value: Any) -> Any:
        """Process the input value according to the processor's configuration.
        
        Args:
            value: The value to process
            
        Returns:
            The processed value
        """
        # Preprocess
        value = self._preprocess(value)
        
        # Convert and validate
        try:
            result = self._convert(value)
        except (ValueError, TypeError):
            return self.default
        
        # Validate the converted value
        if not self._validate(result):
            return self.default
        
        return result
    
    @abstractmethod
    def _convert(self, value: Any) -> Any:
        """Convert the preprocessed value to the target type.
        
        Args:
            value: The preprocessed value to convert
            
        Returns:
            The converted value
        """
        pass


class StringProcessor(BaseProcessor):
    """Processor for string values."""
    
    def _convert(self, value: Any) -> Optional[str]:
        """Convert the input value to a string.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted string or None
        """
        if value is None:
            return None
        
        return str(value)


class NumberProcessor(BaseProcessor):
    """Processor for numeric values."""
    
    def __init__(self, config: ProcessorConfig) -> None:
        """Initialize the number processor.
        
        Args:
            config: Configuration dictionary for the processor
        """
        super().__init__(config)
        self.is_integer = config.get("format") == "integer"
    
    def _convert(self, value: Any) -> Optional[Union[int, float]]:
        """Convert the input value to a number.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted number or None
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return int(value) if self.is_integer else value
        
        if isinstance(value, str):
            # Remove non-numeric characters except decimal point and minus sign
            clean_value = re.sub(r"[^\d.-]", "", value)
            
            if not clean_value:
                return None
            
            try:
                if self.is_integer:
                    # For integers, remove decimal part
                    if "." in clean_value:
                        clean_value = clean_value.split(".")[0]
                    return int(clean_value)
                return float(clean_value)
            except ValueError:
                return None
        
        return None


class DateProcessor(BaseProcessor):
    """Processor for date values."""
    
    def __init__(self, config: ProcessorConfig) -> None:
        """Initialize the date processor.
        
        Args:
            config: Configuration dictionary for the processor
        """
        super().__init__(config)
        self.format = config.get("format", "%Y-%m-%d")
    
    def _convert(self, value: Any) -> Optional[datetime]:
        """Convert the input value to a datetime object.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted datetime or None
        """
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                return datetime.strptime(value, self.format)
            except ValueError:
                # Try common formats if the specified format doesn't work
                common_formats = [
                    "%Y-%m-%d",
                    "%d/%m/%Y",
                    "%m/%d/%Y",
                    "%Y/%m/%d",
                    "%d-%m-%Y",
                    "%m-%d-%Y",
                    "%d.%m.%Y",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ",
                ]
                
                for fmt in common_formats:
                    if fmt != self.format:  # Skip the already tried format
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
        
        return None


class BooleanProcessor(BaseProcessor):
    """Processor for boolean values."""
    
    def _convert(self, value: Any) -> Optional[bool]:
        """Convert the input value to a boolean.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted boolean or None
        """
        if value is None:
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        if isinstance(value, str):
            value = value.lower().strip()
            true_values = ["true", "yes", "y", "1", "t"]
            false_values = ["false", "no", "n", "0", "f"]
            
            if value in true_values:
                return True
            if value in false_values:
                return False
        
        return None


class ListProcessor(BaseProcessor):
    """Processor for list values."""
    
    def __init__(self, config: ProcessorConfig) -> None:
        """Initialize the list processor.
        
        Args:
            config: Configuration dictionary for the processor
        """
        super().__init__(config)
        self.separator = config.get("list_separator", ",")
        
        # Item processor configuration
        item_processor_config = config.get("list_item_processor", {"type": ProcessorType.STRING})
        processor_type = item_processor_config.get("type", ProcessorType.STRING)
        
        # Create the item processor
        if processor_type == ProcessorType.STRING:
            self.item_processor = StringProcessor(item_processor_config)
        elif processor_type == ProcessorType.NUMBER:
            self.item_processor = NumberProcessor(item_processor_config)
        elif processor_type == ProcessorType.DATE:
            self.item_processor = DateProcessor(item_processor_config)
        elif processor_type == ProcessorType.BOOLEAN:
            self.item_processor = BooleanProcessor(item_processor_config)
        else:
            self.item_processor = StringProcessor({"type": ProcessorType.STRING})
    
    def _convert(self, value: Any) -> Optional[List[Any]]:
        """Convert the input value to a list.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted list or None
        """
        if value is None:
            return None
        
        # Already a list
        if isinstance(value, list):
            return [self.item_processor.process(item) for item in value]
        
        # String to be split
        if isinstance(value, str):
            items = [item.strip() for item in value.split(self.separator)]
            return [self.item_processor.process(item) for item in items if item]
        
        # Single item to be wrapped in a list
        return [self.item_processor.process(value)]


class CustomProcessor(BaseProcessor):
    """Processor that uses a custom function."""
    
    def __init__(self, config: ProcessorConfig) -> None:
        """Initialize the custom processor.
        
        Args:
            config: Configuration dictionary for the processor
        """
        super().__init__(config)
        
        # The function name to use
        self.function_name = config.get("custom_function", "")
        
        # Dictionary of available functions
        self.function_map: Dict[str, Callable[[Any], Any]] = {
            "capitalize": lambda x: x.capitalize() if isinstance(x, str) else x,
            "title_case": lambda x: x.title() if isinstance(x, str) else x,
            "remove_html": lambda x: re.sub(r"<[^<]+?>", "", x) if isinstance(x, str) else x,
            "extract_digits": lambda x: re.sub(r"\D", "", x) if isinstance(x, str) else x,
            "normalize_whitespace": lambda x: re.sub(r"\s+", " ", x).strip() if isinstance(x, str) else x,
            "currency_to_number": lambda x: float(re.sub(r"[^\d.]", "", x)) if isinstance(x, str) and re.search(r"\d", x) else x,
        }
    
    def _convert(self, value: Any) -> Any:
        """Apply the custom function to the value.
        
        Args:
            value: The value to process
            
        Returns:
            The processed value
        """
        if value is None:
            return None
        
        func = self.function_map.get(self.function_name)
        if not func:
            return value
        
        try:
            return func(value)
        except Exception:
            return value


class DataProcessor:
    """Main data processor class for processing extracted data."""
    
    def __init__(self, processing_config: Dict[str, ProcessorConfig]) -> None:
        """Initialize the data processor with a configuration map.
        
        Args:
            processing_config: A dictionary mapping field names to processor configurations
        """
        self.processors: Dict[str, BaseProcessor] = {}
        
        # Create processors based on config
        for field_name, config in processing_config.items():
            processor_type = config.get("type", ProcessorType.STRING)
            
            if processor_type == ProcessorType.STRING:
                self.processors[field_name] = StringProcessor(config)
            elif processor_type == ProcessorType.NUMBER:
                self.processors[field_name] = NumberProcessor(config)
            elif processor_type == ProcessorType.DATE:
                self.processors[field_name] = DateProcessor(config)
            elif processor_type == ProcessorType.BOOLEAN:
                self.processors[field_name] = BooleanProcessor(config)
            elif processor_type == ProcessorType.LIST:
                self.processors[field_name] = ListProcessor(config)
            elif processor_type == ProcessorType.CUSTOM:
                self.processors[field_name] = CustomProcessor(config)
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process all fields in the input data.
        
        Args:
            data: Dictionary of field names and their extracted values
            
        Returns:
            A dictionary with field names and their processed values
        """
        result: Dict[str, Any] = {}
        
        # Process each field
        for field_name, processor in self.processors.items():
            if field_name in data:
                result[field_name] = processor.process(data[field_name])
            else:
                # If field doesn't exist in data, use the default value
                result[field_name] = processor.default
        
        # Include any fields from data that don't have processors
        for field_name, value in data.items():
            if field_name not in self.processors:
                result[field_name] = value
        
        return result 