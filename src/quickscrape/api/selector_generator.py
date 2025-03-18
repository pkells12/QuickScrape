"""
Natural language selector generator for QuickScrape.

This module provides functionality to generate CSS selectors from natural language
descriptions using the Claude API.
"""

import logging
import os
from typing import Dict, List, Optional, Union

from quickscrape.api.claude import ClaudeAPIClient, ClaudeConfig, ClaudeModel
from quickscrape.config.models import ScraperConfig
from quickscrape.scraper.base import BaseScraper
from quickscrape.scraper.factory import create_scraper

# Setup logging
logger = logging.getLogger(__name__)


class SelectorGenerator:
    """
    Generator for CSS selectors using natural language descriptions and Claude AI.
    
    This class facilitates the creation of CSS selectors from natural language
    descriptions of web page elements, using the Claude API for interpretation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the selector generator.
        
        Args:
            api_key: Claude API key. If None, will try to read from environment.
            
        Raises:
            ValueError: If no API key is provided and none found in environment.
        """
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Claude API key must be provided or set in CLAUDE_API_KEY environment variable"
            )
        
        # Default configuration for Claude API
        self.claude_config = ClaudeConfig(
            api_key=self.api_key,
            model=ClaudeModel.CLAUDE_3_HAIKU,  # Using the smallest/fastest model for cost efficiency
            temperature=0.0,  # Zero temperature for deterministic responses
            max_tokens=100,   # Small token limit for simple selector responses
        )
        
        logger.debug("Initialized SelectorGenerator")
    
    def generate_selectors(
        self, config: ScraperConfig, url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate CSS selectors for fields from natural language descriptions.
        
        Args:
            config: The scraper configuration containing selector descriptions.
            url: Optional URL to use instead of the one in config.
            
        Returns:
            Dictionary mapping field names to generated CSS selectors.
            
        Raises:
            ValueError: If config contains no selector descriptions.
        """
        if not hasattr(config, "selector_descriptions") or not config.selector_descriptions:
            raise ValueError("Scraper config must contain selector_descriptions")
        
        target_url = url or config.url
        logger.info(f"Generating selectors for URL: {target_url}")
        
        # Create a scraper to fetch the HTML content
        scraper = create_scraper(target_url, config.backend)
        html_content = scraper.get_html(target_url)
        
        # Generate selectors using Claude API
        with ClaudeAPIClient(config=self.claude_config) as claude_client:
            selectors = claude_client.generate_selectors_from_config(config, html_content)
        
        logger.info(f"Generated {len(selectors)} selectors from natural language descriptions")
        return selectors
    
    def update_config_with_selectors(
        self, config: ScraperConfig, url: Optional[str] = None
    ) -> ScraperConfig:
        """
        Update a scraper config with selectors generated from natural language descriptions.
        
        Args:
            config: The scraper configuration to update.
            url: Optional URL to use instead of the one in config.
            
        Returns:
            Updated scraper configuration with generated selectors.
        """
        selectors = self.generate_selectors(config, url)
        
        # Create a copy of the config to avoid modifying the original
        updated_config = ScraperConfig(**config.dict())
        
        # Update selectors in the config
        for field, selector in selectors.items():
            if selector:  # Only update if a non-empty selector was generated
                updated_config.selectors[field] = selector
        
        return updated_config
    
    def interactive_selector_generation(
        self, url: str, field_descriptions: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Generate selectors for a URL with provided field descriptions.
        
        This is a convenience method for generating selectors without
        an existing ScraperConfig object.
        
        Args:
            url: The URL to scrape.
            field_descriptions: Dictionary mapping field names to descriptions.
            
        Returns:
            Dictionary mapping field names to generated CSS selectors.
        """
        # Create a temporary config
        temp_config = ScraperConfig(
            url=url,
            selectors={},
            selector_descriptions=field_descriptions,
            output={"format": "csv", "path": "output.csv"}
        )
        
        return self.generate_selectors(temp_config, url) 