"""
Claude API client for QuickScrape.

This module provides a client for interacting with the Claude AI API,
enabling natural language processing capabilities for selector generation.
"""

import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field, HttpUrl, validator

from quickscrape.config.models import ScraperConfig

# Setup logging
logger = logging.getLogger(__name__)


class ClaudeModel(str, Enum):
    """
    Available Claude AI models.
    """
    CLAUDE_3_OPUS = "claude-3-opus-20240229"  
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


class ClaudeConfig(BaseModel):
    """
    Configuration for Claude API.
    """
    api_key: str = Field(..., description="Claude API key")
    model: ClaudeModel = Field(default=ClaudeModel.CLAUDE_3_HAIKU, description="Claude model to use")
    max_tokens: int = Field(default=1000, description="Maximum tokens in the response")
    temperature: float = Field(default=0.0, description="Temperature for response generation")
    base_url: HttpUrl = Field(default="https://api.anthropic.com", description="Base URL for Claude API")
    
    @validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v
    
    @validator("max_tokens")
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max_tokens is positive."""
        if v <= 0:
            raise ValueError("max_tokens must be positive")
        return v


class ClaudeAPIClient:
    """
    Client for interacting with the Claude AI API.
    
    This client provides methods to generate selectors from natural language
    descriptions and understand web page structure.
    """
    
    def __init__(self, config: Optional[ClaudeConfig] = None, api_key: Optional[str] = None):
        """
        Initialize the Claude API client.
        
        Args:
            config: Configuration for the Claude API.
            api_key: API key for Claude (can be provided directly or via config).
        
        Raises:
            ValueError: If neither config nor api_key is provided.
        """
        if config:
            self.config = config
        elif api_key:
            self.config = ClaudeConfig(api_key=api_key)
        else:
            raise ValueError("Either config or api_key must be provided")
        
        self.client = httpx.Client(
            base_url=str(self.config.base_url),
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=60.0,
        )
        
        logger.debug(f"Initialized Claude API client with model {self.config.model}")
    
    def close(self) -> None:
        """
        Close the client session.
        """
        self.client.close()
    
    def __enter__(self):
        """
        Enable context manager usage.
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the client session when exiting context.
        """
        self.close()
    
    def _prepare_message(self, html_content: str, description: str) -> Dict[str, Any]:
        """
        Prepare a message payload for the Claude API.
        
        Args:
            html_content: HTML content of the page.
            description: Natural language description of elements to find.
            
        Returns:
            Dict containing the API request payload.
        """
        prompt = f"""
        I need your help creating a CSS selector for a web scraping task.
        
        Here's the HTML of the page I want to scrape:
        ```html
        {html_content[:15000]}  # Truncate to avoid token limits
        ```
        
        I want to extract elements that match this description:
        {description}
        
        Please provide a CSS selector that will accurately target these elements.
        Return ONLY the CSS selector string, without any additional explanation.
        """
        
        return {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }
    
    def generate_selector(self, html_content: str, description: str) -> str:
        """
        Generate a CSS selector from a natural language description.
        
        Args:
            html_content: HTML content of the page.
            description: Natural language description of elements to find.
            
        Returns:
            A CSS selector string.
            
        Raises:
            Exception: If API call fails.
        """
        try:
            logger.info(f"Generating selector for: {description}")
            
            payload = self._prepare_message(html_content, description)
            response = self.client.post("/v1/messages", json=payload)
            response.raise_for_status()
            
            data = response.json()
            selector = data["content"][0]["text"].strip()
            
            logger.info(f"Generated selector: {selector}")
            return selector
        
        except Exception as e:
            logger.error(f"Error generating selector: {str(e)}")
            raise
    
    def generate_selectors_from_config(
        self, config: ScraperConfig, html_content: str
    ) -> Dict[str, str]:
        """
        Generate CSS selectors for all fields in a scraper config using natural language.
        
        Args:
            config: The scraper configuration.
            html_content: HTML content of the page.
            
        Returns:
            Dictionary mapping field names to generated CSS selectors.
        """
        selectors = {}
        
        if not hasattr(config, "selector_descriptions"):
            logger.warning("Config lacks selector_descriptions; cannot generate selectors")
            return {}
        
        for field, description in config.selector_descriptions.items():
            try:
                selectors[field] = self.generate_selector(html_content, description)
            except Exception as e:
                logger.error(f"Failed to generate selector for {field}: {str(e)}")
                selectors[field] = ""
        
        return selectors 