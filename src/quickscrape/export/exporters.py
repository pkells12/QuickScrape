"""Export implementations for QuickScrape.

This module provides concrete implementations of data exporters for various formats.
"""

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO, TextIO, Callable, cast
from abc import ABC, abstractmethod

from quickscrape.export.base import Exporter, ExportFormat, ExportError

# Setup logger
logger = logging.getLogger("quickscrape.export.exporters")


class BaseExporter(ABC):
    """Base class for all exporters.
    
    All specific format exporters should inherit from this class
    and implement the required methods.
    """
    
    @abstractmethod
    def export_to_file(self, data: List[Dict[str, Any]], filepath: Union[str, Path]) -> None:
        """Export data to a file.
        
        Args:
            data: The data to export
            filepath: The path to the output file
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        pass
    
    @abstractmethod
    def export_to_string(self, data: List[Dict[str, Any]]) -> str:
        """Export data to a string.
        
        Args:
            data: The data to export
            
        Returns:
            The exported data as a string
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        pass
    
    @abstractmethod
    def export_to_stream(self, data: List[Dict[str, Any]], stream: Union[TextIO, BinaryIO]) -> None:
        """Export data to a stream.
        
        Args:
            data: The data to export
            stream: The stream to write to
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        pass


class CsvExporter(BaseExporter):
    """CSV format exporter.
    
    Exports data as comma-separated values.
    """
    
    def __init__(
        self,
        pretty: bool = True,
        encoding: str = "utf-8",
        delimiter: str = ",",
        include_headers: bool = True,
    ) -> None:
        """Initialize the CSV exporter.
        
        Args:
            pretty: Whether to format the output for human readability
            encoding: Character encoding to use
            delimiter: Field delimiter character
            include_headers: Whether to include column headers
        """
        super().__init__()
        self.delimiter = delimiter
        self.include_headers = include_headers
        self.encoding = encoding
    
    def export_to_file(self, data: List[Dict[str, Any]], filepath: Union[str, Path]) -> None:
        """Export data to a CSV file.
        
        Args:
            data: List of dictionaries representing the scraped items
            filepath: Path to the output file
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, "w", newline="", encoding=self.encoding) as f:
                self.export_to_stream(data, f)
            logger.info(f"Data exported to CSV file: {filepath}")
        except Exception as e:
            logger.error(f"Error writing to CSV file {filepath}: {e}")
            raise ExportError(f"Failed to export data to CSV file: {e}")
    
    def export_to_string(self, data: List[Dict[str, Any]]) -> str:
        """Export data to a CSV string.
        
        Args:
            data: List of dictionaries representing the scraped items
            
        Returns:
            CSV string representation of the data
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        try:
            output = io.StringIO()
            self.export_to_stream(data, output)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error converting data to CSV string: {e}")
            raise ExportError(f"Failed to export data to CSV string: {e}")
    
    def export_to_stream(self, data: List[Dict[str, Any]], stream: Union[TextIO, BinaryIO]) -> None:
        """Export data to a stream in CSV format.
        
        Args:
            data: List of dictionaries representing the scraped items
            stream: Output stream to write to
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        try:
            if not data:
                logger.warning("No data to export to CSV")
                return
            
            # Initialize CSV writer
            text_stream = cast(TextIO, stream)
            writer = csv.writer(text_stream, delimiter=self.delimiter)
            
            # Get all possible field names across all items
            fieldnames: set[str] = set()
            for item in data:
                fieldnames.update(item.keys())
            
            # Sort fieldnames for consistent output
            sorted_fieldnames = sorted(fieldnames)
            
            # Write header if requested
            if self.include_headers:
                writer.writerow(sorted_fieldnames)
            
            # Write data rows
            for item in data:
                row = [str(item.get(field, "")) for field in sorted_fieldnames]
                writer.writerow(row)
        except Exception as e:
            logger.error(f"Error writing to CSV stream: {e}")
            raise ExportError(f"Failed to export data to CSV stream: {e}")


class JsonExporter(BaseExporter):
    """JSON format exporter.
    
    Exports data as JSON objects.
    """
    
    def __init__(self, pretty: bool = True, encoding: str = "utf-8") -> None:
        """Initialize the JSON exporter.
        
        Args:
            pretty: Whether to pretty-print the JSON
            encoding: The encoding to use for the JSON
        """
        super().__init__()
        self.pretty = pretty
        self.encoding = encoding
    
    def export_to_file(self, data: List[Dict[str, Any]], filepath: Union[str, Path]) -> None:
        """Export data to a JSON file.
        
        Args:
            data: List of dictionaries representing the scraped items
            filepath: Path to the output file
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, "w", encoding=self.encoding) as f:
                json_str = self.export_to_string(data)
                f.write(json_str)
            logger.info(f"Data exported to JSON file: {filepath}")
        except Exception as e:
            logger.error(f"Error writing to JSON file {filepath}: {e}")
            raise ExportError(f"Failed to export data to JSON file: {e}")
    
    def export_to_string(self, data: List[Dict[str, Any]]) -> str:
        """Export data to a JSON string.
        
        Args:
            data: List of dictionaries representing the scraped items
            
        Returns:
            JSON string representation of the data
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        try:
            if not data:
                logger.warning("No data to export to JSON")
                return "[]"
            
            indent = 2 if self.pretty else None
            return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error converting data to JSON string: {e}")
        if not data:
            logger.warning("No data to export to JSON")
            return "[]"
        
        indent = 2 if self.pretty else None
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    
    def export_to_stream(self, data: List[Dict[str, Any]], stream: Union[TextIO, BinaryIO]) -> None:
        """Export data to a stream in JSON format.
        
        Args:
            data: List of dictionaries representing the scraped items
            stream: Output stream to write to
            
        Raises:
            IOError: If there's an error writing to the stream
        """
        json_str = self.export_to_string(data)
        text_stream = cast(TextIO, stream)
        text_stream.write(json_str)


class ExcelExporter(BaseExporter):
    """Exporter for Excel data format."""
    
    def __init__(
        self,
        pretty: bool = True,
        encoding: str = "utf-8",
        sheet_name: str = "Data",
        include_headers: bool = True,
    ) -> None:
        """Initialize the Excel exporter.
        
        Args:
            pretty: Whether to pretty print the output
            encoding: The encoding to use
            sheet_name: The name of the sheet in the Excel file
            include_headers: Whether to include headers
        """
        super().__init__()
        self.sheet_name = sheet_name
        self.include_headers = include_headers
        self.encoding = encoding
        
        # Import pandas lazily to avoid dependency if not used
        try:
            import pandas as pd
            self._pd = pd
        except ImportError:
            self._pd = None
    
    def _ensure_pandas(self) -> None:
        """Ensure pandas is available.
        
        Raises:
            ImportError: If pandas is not installed
        """
        if self._pd is None:
            raise ImportError(
                "Pandas is required for Excel export. "
                "Install it with 'pip install pandas openpyxl'"
            )
    
    def export_to_file(self, data: List[Dict[str, Any]], filepath: Union[str, Path]) -> None:
        """Export data to an Excel file.
        
        Args:
            data: List of dictionaries representing the scraped items
            filepath: Path to the output file
            
        Raises:
            ExportError: If there's an error exporting the data
        """
        try:
            # Import pandas here to avoid requiring it as a dependency
            import pandas as pd
            
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            
            # Write to Excel file
            df.to_excel(
                filepath,
                sheet_name=self.sheet_name,
                index=False,
                header=True
            )
            
            logger.info(f"Data exported to Excel file {filepath}")
        except Exception as e:
            logger.error(f"Error writing to Excel file {filepath}: {e}")
            raise ExportError(f"Failed to export data to Excel file: {e}")
    
    def export_to_string(self, data: List[Dict[str, Any]]) -> str:
        """Export data to a string.
        
        For Excel format, this returns a CSV representation as Excel files are binary.
        
        Args:
            data: List of dictionaries representing the scraped items
            
        Returns:
            CSV string representation of the data
            
        Raises:
            ImportError: If pandas is not installed
        """
        self._ensure_pandas()
        
        if not data:
            logger.warning("No data to export to string")
            return ""
        
        # Use pandas to convert to CSV string as a fallback
        df = self._pd.DataFrame(data)
        return df.to_csv(index=False, header=self.include_headers)
    
    def export_to_stream(self, data: List[Dict[str, Any]], stream: Union[TextIO, BinaryIO]) -> None:
        """Export data to a stream in Excel format.
        
        Args:
            data: List of dictionaries representing the scraped items
            stream: Output binary stream to write to
            
        Raises:
            IOError: If there's an error writing to the stream
            ImportError: If pandas is not installed
            TypeError: If stream is not a binary stream
        """
        self._ensure_pandas()
        
        # Excel requires a binary stream
        binary_stream = cast(BinaryIO, stream)
        
        if not data:
            logger.warning("No data to export to Excel stream")
            # Write an empty Excel workbook
            self._pd.DataFrame().to_excel(
                binary_stream, sheet_name=self.sheet_name, index=False
            )
            return
        
        # Convert data to DataFrame
        df = self._pd.DataFrame(data)
        
        # Write to Excel binary stream
        with io.BytesIO() as output:
            df.to_excel(
                output,
                sheet_name=self.sheet_name,
                index=False,
                header=self.include_headers,
            )
            binary_stream.write(output.getvalue())


def create_exporter(
    format_type: Union[str, ExportFormat],
    pretty: bool = True,
    encoding: str = "utf-8",
    **kwargs: Any,
) -> BaseExporter:
    """Create an exporter for the specified format.
    
    Args:
        format_type: The format to export to
        pretty: Whether to pretty print the output
        encoding: The encoding to use
        **kwargs: Additional format-specific options
        
    Returns:
        An exporter for the specified format
        
    Raises:
        ValueError: If the format is invalid
    """
    # Convert string format to enum if needed
    if isinstance(format_type, str):
        format_type = ExportFormat.from_string(format_type)
    
    # Create appropriate exporter based on format
    if format_type == ExportFormat.CSV:
        return CsvExporter(
            pretty=pretty,
            encoding=encoding,
            delimiter=kwargs.get("delimiter", ","),
            include_headers=kwargs.get("include_headers", True),
        )
    elif format_type == ExportFormat.JSON:
        return JsonExporter(pretty=pretty, encoding=encoding)
    elif format_type == ExportFormat.EXCEL:
        return ExcelExporter(
            pretty=pretty,
            encoding=encoding,
            sheet_name=kwargs.get("sheet_name", "Data"),
            include_headers=kwargs.get("include_headers", True),
        )
    else:
        raise ValueError(f"Unsupported export format: {format_type}") 