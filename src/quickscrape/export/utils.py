"""Export utilities for QuickScrape.

This module provides utility functions for data export operations.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from quickscrape.export.base import Exporter, ExportFormat
from quickscrape.export.config import ExportConfig
from quickscrape.export.exporters import create_exporter

logger = logging.getLogger(__name__)


def export_data(
    data: List[Dict[str, Any]],
    config_name: str,
    export_config: Optional[ExportConfig] = None,
    filepath: Optional[Union[str, Path]] = None,
) -> str:
    """Export data to a file based on configuration.
    
    Args:
        data: List of dictionaries representing the scraped items
        config_name: Name of the scraping configuration used
        export_config: Export configuration (uses defaults if None)
        filepath: Specific filepath to export to (overrides config path generation)
    
    Returns:
        Path to the exported file
        
    Raises:
        IOError: If there's an error during export
        ValueError: If the export format is invalid
        ImportError: If necessary dependencies aren't installed
    """
    # Use default export config if none provided
    if export_config is None:
        export_config = ExportConfig()
    
    # Generate output path if not specified
    output_path = filepath if filepath else export_config.get_output_filepath(config_name)
    
    # Create exporter for the specified format
    exporter_kwargs = export_config.get_exporter_kwargs()
    exporter = create_exporter(export_config.format, **exporter_kwargs)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.debug(f"Created output directory: {output_dir}")
    
    # Export data
    logger.info(f"Exporting {len(data)} items to {output_path} in {export_config.format.name} format")
    exporter.export_to_file(data, output_path)
    
    return output_path


def export_data_to_string(
    data: List[Dict[str, Any]],
    export_format: Union[str, ExportFormat] = "json",
    **kwargs: Any,
) -> str:
    """Export data to a string in the specified format.
    
    Args:
        data: List of dictionaries representing the scraped items
        export_format: Format to export data in
        **kwargs: Format-specific options
        
    Returns:
        String representation of the exported data
        
    Raises:
        ValueError: If the export format is invalid
        ImportError: If necessary dependencies aren't installed
    """
    exporter = create_exporter(export_format, **kwargs)
    return exporter.export_to_string(data) 