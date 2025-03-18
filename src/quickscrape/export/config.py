"""Export configuration for QuickScrape.

This module provides configuration classes and validation for export settings.
"""

import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from quickscrape.export.base import ExportFormat


class ExportConfig(BaseModel):
    """Configuration for data export operations."""
    
    format: ExportFormat = Field(
        default=ExportFormat.JSON,
        description="Format to export data in"
    )
    
    output_path: str = Field(
        default="./output",
        description="Directory to write output files to"
    )
    
    filename_template: str = Field(
        default="{config_name}_{timestamp}.{extension}",
        description="Template for generating output filenames"
    )
    
    pretty: bool = Field(
        default=True,
        description="Whether to format the output for human readability"
    )
    
    encoding: str = Field(
        default="utf-8",
        description="Character encoding to use for text-based exports"
    )
    
    # Format-specific options
    csv_delimiter: str = Field(
        default=",",
        description="Field delimiter for CSV export"
    )
    
    include_headers: bool = Field(
        default=True,
        description="Whether to include column headers in tabular exports"
    )
    
    excel_sheet_name: str = Field(
        default="Data",
        description="Sheet name for Excel export"
    )
    
    @validator("format", pre=True)
    def validate_format(cls, v: Any) -> ExportFormat:
        """Validate and convert export format.
        
        Args:
            v: Input format value
            
        Returns:
            Validated ExportFormat enum
            
        Raises:
            ValueError: If the format is invalid
        """
        if isinstance(v, ExportFormat):
            return v
        if isinstance(v, str):
            return ExportFormat.from_string(v)
        raise ValueError(f"Invalid export format: {v}")
    
    def get_output_filepath(self, config_name: str) -> str:
        """Generate output filepath based on configuration.
        
        Args:
            config_name: Name of the scraping configuration
            
        Returns:
            Generated output filepath
        """
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get file extension
        extension = self.format.file_extension
        
        # Fill in template
        filename = self.filename_template.format(
            config_name=config_name,
            timestamp=timestamp,
            extension=extension,
            date=datetime.now().strftime("%Y-%m-%d"),
            time=datetime.now().strftime("%H-%M-%S")
        )
        
        # Join with output path
        return os.path.join(self.output_path, filename)
    
    def get_exporter_kwargs(self) -> Dict[str, Any]:
        """Get format-specific exporter parameters.
        
        Returns:
            Dictionary of parameters for the exporter
        """
        common_kwargs = {
            "pretty": self.pretty,
            "encoding": self.encoding,
        }
        
        if self.format == ExportFormat.CSV:
            return {
                **common_kwargs,
                "delimiter": self.csv_delimiter,
                "include_headers": self.include_headers,
            }
        elif self.format == ExportFormat.EXCEL:
            return {
                **common_kwargs,
                "sheet_name": self.excel_sheet_name,
                "include_headers": self.include_headers,
            }
        else:  # JSON or other formats
            return common_kwargs 