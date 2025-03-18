"""
Factory for creating scrapers based on configuration.

This module provides functions for determining the appropriate scraper
implementation to use based on the configuration and website characteristics.
"""

import re
from typing import Optional, Type

import requests
from bs4 import BeautifulSoup

from quickscrape.config.models import BackendType, ScraperConfig
from quickscrape.scraper.base import BaseScraper
from quickscrape.scraper.requests_scraper import RequestsScraper
from quickscrape.scraper.playwright_scraper import PlaywrightScraper
from quickscrape.utils.logger import get_logger

logger = get_logger(__name__)


def create_scraper(config: ScraperConfig) -> BaseScraper:
    """
    Create an appropriate scraper based on the configuration.
    
    This function determines which scraper implementation to use based on
    the configuration's backend setting, with AUTO detection if necessary.
    
    Args:
        config: The scraper configuration
        
    Returns:
        BaseScraper: An instance of the appropriate scraper implementation
    """
    backend = config.backend or BackendType.AUTO
    
    # If backend is explicitly specified, use it
    if backend != BackendType.AUTO:
        return _create_scraper_for_backend(backend, config)
    
    # Otherwise, try to auto-detect the appropriate backend
    detected_backend = auto_detect_backend(config)
    logger.debug(f"Auto-detected backend: {detected_backend}")
    
    return _create_scraper_for_backend(detected_backend, config)


def _create_scraper_for_backend(backend: BackendType, config: ScraperConfig) -> BaseScraper:
    """
    Create a scraper for the specified backend type.
    
    Args:
        backend: The backend type to use
        config: The scraper configuration
        
    Returns:
        BaseScraper: An instance of the appropriate scraper implementation
    """
    if backend == BackendType.PLAYWRIGHT:
        return PlaywrightScraper(config)
    else:
        # Default to requests-based scraper
        return RequestsScraper(config)


def auto_detect_backend(config: ScraperConfig) -> BackendType:
    """
    Auto-detect the most appropriate backend for the given configuration.
    
    This function attempts to determine if the target website requires JavaScript
    rendering by examining its content and behavior.
    
    Args:
        config: The scraper configuration
        
    Returns:
        BackendType: The detected backend type
    """
    url = config.url
    
    try:
        # Default user agent if none provided
        headers = config.headers or {}
        if config.user_agent:
            headers['User-Agent'] = config.user_agent
        
        # Make a request to the URL
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Check for signs of JavaScript-heavy content
        needs_js = _check_if_needs_javascript(soup, url)
        
        if needs_js:
            logger.debug(f"Detected that {url} needs JavaScript, using Playwright backend")
            return BackendType.PLAYWRIGHT
        else:
            logger.debug(f"No JavaScript requirement detected for {url}, using Requests backend")
            return BackendType.REQUESTS
    
    except Exception as e:
        logger.warning(f"Error during backend auto-detection: {str(e)}")
        # Default to Playwright as a safer choice when detection fails
        return BackendType.PLAYWRIGHT


def _check_if_needs_javascript(soup: BeautifulSoup, url: str) -> bool:
    """
    Check if the page likely requires JavaScript to render its content.
    
    This function uses heuristics to determine if the page seems to rely
    heavily on JavaScript for content rendering.
    
    Args:
        soup: The parsed HTML content
        url: The URL of the page
        
    Returns:
        bool: True if the page likely needs JavaScript, False otherwise
    """
    # Check if there's minimal content in the body (often a sign of JS rendering)
    body_content = soup.find('body')
    if body_content and len(body_content.get_text(strip=True)) < 500:
        # Look for signs of JS frameworks
        all_scripts = soup.find_all('script')
        script_contents = ' '.join([s.get_text() for s in all_scripts if s.get_text()])
        
        js_frameworks = [
            'react', 'vue', 'angular', 'ember', 'svelte', 'backbone',
            'jquery', 'axios', 'fetch', 'xhr', 'ajax', 'graphql',
            'renderer', 'rendering', 'hydrate'
        ]
        
        if any(framework in script_contents.lower() for framework in js_frameworks):
            return True
    
    # Check for AJAX-loaded content
    if len(soup.find_all('div', {'id': re.compile('app|root|container')})) > 0:
        return True
    
    # Check for infinite scroll indicators
    if len(soup.find_all(string=re.compile('load more|infinite scroll|show more'))) > 0:
        return True
    
    # Check for common JS load indicators
    if len(soup.find_all('div', {'class': re.compile('loader|spinner|loading')})) > 0:
        return True
    
    # Look for React or other JS framework signatures
    if len(soup.find_all(attrs={'data-reactroot': True})) > 0:
        return True
    
    # Check for lazy-loaded images
    lazy_images = soup.find_all('img', {'loading': 'lazy'})
    if lazy_images and len(lazy_images) > 5:
        return True
    
    # For e-commerce and certain other sites, better to use Playwright
    ecommerce_indicators = ['cart', 'checkout', 'product', 'shop', 'store', 'price']
    page_text = soup.get_text().lower()
    if any(indicator in url.lower() or indicator in page_text for indicator in ecommerce_indicators):
        # Check if there are product listings that might need JS
        if len(soup.find_all(class_=re.compile('product|item|card'))) > 5:
            return True
    
    return False 