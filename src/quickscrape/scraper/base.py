"""
Base scraper implementation for QuickScrape.

This module provides the base abstract class for all scraper backends.
"""

import abc
import time
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from quickscrape.config.models import PaginationConfig, ScraperConfig
from quickscrape.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class ScrapeResult(BaseModel):
    """
    Model representing the result of a scraping operation.
    
    Contains the extracted data and metadata about the scraping process.
    """
    items: List[Dict[str, Any]]
    url: str
    pages_scraped: int
    total_items: int
    success: bool
    error: Optional[str] = None
    duration_seconds: float


class BaseScraper(abc.ABC):
    """
    Base abstract class for all scraper implementations.
    
    Provides common functionality for configuring and running scrapers,
    while leaving the actual scraping implementation to concrete subclasses.
    """
    
    def __init__(self, config: ScraperConfig) -> None:
        """
        Initialize the scraper with the given configuration.
        
        Args:
            config: The scraper configuration
        """
        self.config = config
        self.url = config.url
        self.selectors = config.selectors
        self.wait_time = config.wait_time or 0.5
        self.user_agent = config.user_agent
        self.headers = config.headers or {}
        self.pagination = config.pagination
        
        # Set up default headers if not provided
        if not self.user_agent and "User-Agent" not in self.headers:
            self._setup_default_headers()
            
        # Random delays for anti-bot measures
        self.random_delay = True
        
        logger.debug(f"Initialized {self.__class__.__name__} with URL: {self.url}")
    
    def _setup_default_headers(self) -> None:
        """
        Set up default headers for HTTP requests.
        
        This helps avoid being blocked by some websites that check for common headers.
        """
        default_ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        if "User-Agent" not in self.headers:
            self.headers["User-Agent"] = default_ua
            
        if "Accept" not in self.headers:
            self.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            
        if "Accept-Language" not in self.headers:
            self.headers["Accept-Language"] = "en-US,en;q=0.5"
    
    def scrape(self) -> ScrapeResult:
        """
        Execute the scraping process using the configured settings.
        
        This method orchestrates the entire scraping workflow, including
        pagination handling and combining results.
        
        Returns:
            ScrapeResult: Object containing the scraped data and metadata
        """
        start_time = time.time()
        all_items: List[Dict[str, Any]] = []
        current_url = self.url
        page_count = 0
        error = None
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Scraping {self.url}...", total=None)
                
                # Initial connection and scraping
                self._before_scrape()
                
                # Main scraping loop for pagination
                while True:
                    # Delay to avoid overloading the server
                    self._delay()
                    
                    # Update progress
                    page_count += 1
                    progress.update(task, description=f"Scraping page {page_count}...")
                    
                    # Perform the actual scraping
                    logger.debug(f"Scraping page {page_count}: {current_url}")
                    page_items = self._scrape_page(current_url)
                    all_items.extend(page_items)
                    
                    # Check pagination
                    if not self._should_continue_pagination(page_count):
                        logger.debug(f"Reached pagination limit at page {page_count}")
                        break
                    
                    # Get next page URL
                    next_url = self._get_next_page_url(current_url, page_count)
                    if not next_url:
                        logger.debug("No next page found, ending pagination")
                        break
                    
                    current_url = next_url
                
                # Cleanup after scraping
                self._after_scrape()
                
                # Finalize progress bar
                progress.update(task, description=f"Scraped {len(all_items)} items from {page_count} pages")
        
        except Exception as e:
            logger.exception(f"Error during scraping: {str(e)}")
            error = str(e)
        
        duration = time.time() - start_time
        
        return ScrapeResult(
            items=all_items,
            url=self.url,
            pages_scraped=page_count,
            total_items=len(all_items),
            success=error is None,
            error=error,
            duration_seconds=duration
        )
    
    def _should_continue_pagination(self, current_page: int) -> bool:
        """
        Check if pagination should continue based on configured limits.
        
        Args:
            current_page: The current page number (1-indexed)
            
        Returns:
            bool: True if pagination should continue, False otherwise
        """
        # If no pagination is configured, stop after the first page
        if not self.pagination:
            return False
        
        # If a max pages limit is set, check if we've reached it
        if self.pagination.max_pages and current_page >= self.pagination.max_pages:
            return False
        
        return True
    
    def _delay(self) -> None:
        """
        Introduce a delay between requests to avoid overloading the server.
        
        This uses either a fixed delay from the configuration or a randomized
        delay for better anti-bot protection.
        """
        delay = self.wait_time
        
        if self.random_delay:
            # Add a small random component to the delay (±20%)
            import random
            variation = delay * 0.2
            delay = delay + random.uniform(-variation, variation)
            
        logger.debug(f"Waiting for {delay:.2f} seconds before next request")
        time.sleep(delay)
    
    def _before_scrape(self) -> None:
        """
        Perform any setup operations needed before scraping begins.
        
        This is called once at the beginning of the scraping process.
        Can be overridden by subclasses for backend-specific setup.
        """
        pass
    
    def _after_scrape(self) -> None:
        """
        Perform any cleanup operations needed after scraping completes.
        
        This is called once at the end of the scraping process.
        Can be overridden by subclasses for backend-specific cleanup.
        """
        pass
    
    @abc.abstractmethod
    def _scrape_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape a single page and extract data using the configured selectors.
        
        This abstract method must be implemented by all concrete scraper classes.
        
        Args:
            url: The URL of the page to scrape
            
        Returns:
            List[Dict[str, Any]]: List of extracted items, where each item is a 
                                  dictionary of field names to extracted values
        """
        pass
    
    @abc.abstractmethod
    def _get_next_page_url(self, current_url: str, current_page: int) -> Optional[str]:
        """
        Get the URL for the next page based on the pagination configuration.
        
        This abstract method must be implemented by all concrete scraper classes.
        
        Args:
            current_url: The URL of the current page
            current_page: The current page number (1-indexed)
            
        Returns:
            Optional[str]: The URL of the next page, or None if there is no next page
        """
        pass 