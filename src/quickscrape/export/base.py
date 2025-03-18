"""Base export functionality for QuickScrape.

This module provides the base classes and interfaces for exporters.
"""

import abc
import logging
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO, TextIO

logger = logging.getLogger(__name__)


class ExportError(Exception):
    """Exception raised for errors during data export operations."""

    pass


class ExportFormat(Enum):
    """Supported export formats."""
    CSV = auto()
    JSON = auto()
    EXCEL = auto()
    
    @classmethod
    def from_string(cls, format_str: str) -> "ExportFormat":
        """Convert a string to an ExportFormat enum.
        
        Args:
            format_str: String representation of the export format
            
        Returns:
            Corresponding ExportFormat enum value
            
        Raises:
            ValueError: If the format string is not supported
        """
        format_map = {
            "csv": cls.CSV,
            "json": cls.JSON,
            "excel": cls.EXCEL,
            "xlsx": cls.EXCEL,
            "xls": cls.EXCEL
        }
        
        format_str = format_str.lower()
        if format_str not in format_map:
            supported = ", ".join(format_map.keys())
            raise ValueError(f"Unsupported export format: {format_str}. Supported formats: {supported}")
        
        return format_map[format_str]
    
    @property
    def file_extension(self) -> str:
        """Get the file extension for this format.
        
        Returns:
            File extension (without leading dot)
        """
        extension_map = {
            self.CSV: "csv",
            self.JSON: "json",
            self.EXCEL: "xlsx"
        }
        return extension_map[self]


class Exporter(abc.ABC):
    """Base class for data exporters.
    
    This abstract class defines the interface that all exporters must implement.
    """
    
    def __init__(self, pretty: bool = True, encoding: str = "utf-8") -> None:
        """Initialize the exporter.
        
        Args:
            pretty: Whether to format the output for human readability
            encoding: Character encoding to use for text-based exports
        """
        self.pretty = pretty
        self.encoding = encoding
    
    @abc.abstractmethod
    def export_to_file(self, data: List[Dict[str, Any]], filepath: Union[str, Path]) -> None:
        """Export data to a file.
        
        Args:
            data: List of dictionaries representing the scraped items
            filepath: Path to the output file
            
        Raises:
            IOError: If there's an error writing to the file
        """
        pass
    
    @abc.abstractmethod
    def export_to_string(self, data: List[Dict[str, Any]]) -> str:
        """Export data to a string.
        
        Args:
            data: List of dictionaries representing the scraped items
            
        Returns:
            String representation of the exported data
        """
        pass
    
    @abc.abstractmethod
    def export_to_stream(self, data: List[Dict[str, Any]], stream: Union[TextIO, BinaryIO]) -> None:
        """Export data to a stream.
        
        Args:
            data: List of dictionaries representing the scraped items
            stream: Output stream to write to
            
        Raises:
            IOError: If there's an error writing to the stream
        """
        pass
    
    def _ensure_dir_exists(self, filepath: Union[str, Path]) -> None:
        """Ensure the directory for the filepath exists.
        
        Args:
            filepath: Path to check and create directories for if needed
        """
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            logger.debug(f"Created directory: {directory}") 