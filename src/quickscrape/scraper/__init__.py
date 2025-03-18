"""
Scraping engine for QuickScrape.

This package contains the core scraping functionality, including
different backend implementations and data extraction logic.
"""

from quickscrape.scraper.factory import create_scraper
from quickscrape.scraper.base import BaseScraper, ScrapeResult


def run_scraper(scraper: BaseScraper, config: dict) -> list:
    """
    Run a scraper with the given configuration.
    
    Args:
        scraper: The scraper instance to run
        config: The scraper configuration
        
    Returns:
        List of scraped items
        
    Raises:
        Exception: If scraping fails
    """
    result = scraper.scrape()
    
    if not result.success:
        raise Exception(f"Scraping failed: {result.error}")
        
    return result.items


__all__ = ["create_scraper", "BaseScraper", "run_scraper"] 