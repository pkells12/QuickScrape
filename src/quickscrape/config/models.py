"""
Configuration models for QuickScrape.

This module contains Pydantic models that define the structure and validation
for QuickScrape configuration files.
"""

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, validator


class BackendType(str, Enum):
    """
    Available scraping backend types.
    """
    AUTO = "auto"
    REQUESTS = "requests"
    PLAYWRIGHT = "playwright"


class PaginationType(str, Enum):
    """
    Available pagination types.
    """
    NONE = "none"
    URL_PARAM = "url_param"
    NEXT_BUTTON = "next_button"
    LOAD_MORE = "load_more"
    INFINITE_SCROLL = "infinite_scroll"


class OutputFormat(str, Enum):
    """
    Available output formats.
    """
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


class PaginationConfig(BaseModel):
    """
    Configuration for pagination.
    """
    type: PaginationType = Field(default=PaginationType.NONE, description="Type of pagination to use")
    selector: Optional[str] = Field(None, description="CSS selector for the pagination element")
    param_name: Optional[str] = Field(None, description="URL parameter name for pagination")
    max_pages: Optional[int] = Field(None, description="Maximum number of pages to scrape")

    @validator("selector")
    def validate_selector_for_button_types(cls, v, values):
        """Validate that selector is provided for button-based pagination types."""
        if values.get("type") in [PaginationType.NEXT_BUTTON, PaginationType.LOAD_MORE] and not v:
            raise ValueError(f"Selector is required for pagination type: {values.get('type')}")
        return v

    @validator("param_name")
    def validate_param_name_for_url_param(cls, v, values):
        """Validate that param_name is provided for URL parameter pagination."""
        if values.get("type") == PaginationType.URL_PARAM and not v:
            raise ValueError("param_name is required for URL parameter pagination")
        return v


class OutputConfig(BaseModel):
    """
    Configuration for output.
    """
    format: OutputFormat = Field(default=OutputFormat.CSV, description="Output format")
    path: str = Field(..., description="Path to save the output file")
    append: bool = Field(default=False, description="Whether to append to existing file")
    delimiter: Optional[str] = Field(",", description="Delimiter for CSV output")
    encoding: Optional[str] = Field("utf-8", description="File encoding")


class ScraperConfig(BaseModel):
    """
    Main configuration for a scraper.
    """
    url: str = Field(..., description="URL to scrape")
    selectors: Dict[str, str] = Field(..., description="CSS selectors for elements to extract")
    selector_descriptions: Optional[Dict[str, str]] = Field(None, description="Natural language descriptions of elements to extract")
    backend: BackendType = Field(default=BackendType.AUTO, description="Scraping backend to use")
    wait_time: Optional[float] = Field(0.5, description="Time to wait between requests in seconds")
    user_agent: Optional[str] = Field(None, description="User agent string to use")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional HTTP headers")
    pagination: Optional[PaginationConfig] = Field(None, description="Pagination configuration")
    output: OutputConfig = Field(..., description="Output configuration")
    
    @validator("url")
    def validate_url(cls, v):
        """Basic URL validation."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v 