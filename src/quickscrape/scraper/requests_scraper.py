"""
Requests-based scraper implementation for QuickScrape.

This module provides a scraper implementation using the requests library,
which is suitable for static websites without JavaScript requirements.
"""

import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import cloudscraper

from quickscrape.config.models import PaginationType
from quickscrape.scraper.base import BaseScraper
from quickscrape.utils.logger import get_logger

logger = get_logger(__name__)


class RequestsScraper(BaseScraper):
    """
    Scraper implementation using the requests library.
    
    This scraper is suitable for static websites that don't require JavaScript
    execution. It uses BeautifulSoup for HTML parsing and selector processing.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the requests-based scraper.
        
        Args:
            *args: Positional arguments to pass to the parent constructor
            **kwargs: Keyword arguments to pass to the parent constructor
        """
        super().__init__(*args, **kwargs)
        self.session = None
        self.use_cloudscraper = False
        
        # Check if we should use cloudscraper to bypass some anti-bot protections
        if self.config.headers and any(h.lower() == 'cf-challenge' for h in self.config.headers):
            self.use_cloudscraper = True
    
    def _before_scrape(self) -> None:
        """
        Set up the HTTP session before scraping begins.
        
        Creates either a standard requests session or a cloudscraper session
        based on the configuration.
        """
        if self.use_cloudscraper:
            logger.debug("Using CloudScraper to bypass Cloudflare protection")
            self.session = cloudscraper.create_scraper()
        else:
            self.session = requests.Session()
        
        # Add default headers to session
        if self.headers:
            self.session.headers.update(self.headers)
        
        if self.user_agent:
            self.session.headers["User-Agent"] = self.user_agent
    
    def _after_scrape(self) -> None:
        """
        Clean up resources after scraping is complete.
        """
        if self.session:
            self.session.close()
            self.session = None
    
    def _get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch the page content and parse it with BeautifulSoup.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Optional[BeautifulSoup]: Parsed HTML content, or None if the request failed
        """
        try:
            logger.debug(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check for common empty responses or redirects to login pages
            if len(response.text) < 200 or "login" in response.url.lower():
                logger.warning(f"Suspicious response (len={len(response.text)}, URL={response.url})")
                
            return BeautifulSoup(response.text, "html.parser")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def _extract_data_from_selectors(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract data from the parsed HTML using the configured selectors.
        
        Args:
            soup: The parsed HTML content
            
        Returns:
            List[Dict[str, Any]]: List of extracted items
        """
        # Determine if we need to extract multiple items or just one
        # Look for a common parent element if multiple selectors point to list items
        items = []
        single_item = {}
        needs_list_extraction = self._needs_list_extraction(soup)
        
        if needs_list_extraction:
            # Extract a list of items
            container_selector, item_selector = self._find_list_container_and_item(soup)
            
            if container_selector and item_selector:
                container_elements = soup.select(container_selector)
                if container_elements and len(container_elements) > 0:
                    container = container_elements[0]
                    item_elements = container.select(item_selector)
                    
                    for item_element in item_elements:
                        item_data = {}
                        for field, selector in self.selectors.items():
                            # Try to find elements within this item context
                            found = item_element.select(selector)
                            if found:
                                item_data[field] = self._extract_value(found[0])
                        
                        if item_data:
                            items.append(item_data)
            
            # If list extraction failed, fall back to single extraction
            if not items:
                logger.warning("List extraction failed, falling back to single item extraction")
                needs_list_extraction = False
        
        if not needs_list_extraction:
            # Extract a single item with all selectors
            for field, selector in self.selectors.items():
                elements = soup.select(selector)
                if elements:
                    single_item[field] = self._extract_value(elements[0])
            
            if single_item:
                items.append(single_item)
        
        return items
    
    def _needs_list_extraction(self, soup: BeautifulSoup) -> bool:
        """
        Determine if we need to extract multiple items or just one.
        
        Args:
            soup: The parsed HTML content
            
        Returns:
            bool: True if we need to extract multiple items, False otherwise
        """
        # Check if multiple elements match each selector
        selector_counts = {}
        for field, selector in self.selectors.items():
            elements = soup.select(selector)
            selector_counts[field] = len(elements)
        
        # If any selector has multiple matches, we need list extraction
        return any(count > 1 for count in selector_counts.values())
    
    def _find_list_container_and_item(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """
        Try to find a common container and item selector for list extraction.
        
        This is a heuristic approach to identify list structures in HTML.
        
        Args:
            soup: The parsed HTML content
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (container_selector, item_selector) or (None, None) if not found
        """
        # Look for common list containers
        common_containers = [
            ("ul", "li"),
            ("ol", "li"),
            ("table", "tr"),
            ("div.products", "div.product"),
            ("div.items", "div.item"),
            ("div.results", "div.result"),
            ("div.listing", "div.listing-item"),
        ]
        
        for container_tag, item_tag in common_containers:
            container_elements = soup.select(container_tag)
            if container_elements and len(container_elements) > 0:
                container = container_elements[0]
                if container and container.select(item_tag):
                    return container_tag, item_tag
        
        # If no common patterns found, try to be smarter by looking at selector structure
        # This is a simplified approach, can be expanded for better detection
        return None, None
    
    def _extract_value(self, element) -> str:
        """
        Extract the most relevant value from an HTML element.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            str: Extracted value
        """
        # For links, prefer href attribute
        if element.name == "a" and element.get("href"):
            return element["href"]
        
        # For images, prefer src or alt attributes
        if element.name == "img":
            if element.get("src"):
                return element["src"]
            elif element.get("alt"):
                return element["alt"]
        
        # For inputs, prefer value attribute
        if element.name == "input" and element.get("value"):
            return element["value"]
        
        # For most elements, get the text content
        return element.get_text(strip=True)
    
    def _scrape_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape a single page and extract data using the configured selectors.
        
        Args:
            url: The URL of the page to scrape
            
        Returns:
            List[Dict[str, Any]]: List of extracted items
        """
        soup = self._get_page_content(url)
        if not soup:
            logger.error(f"Failed to get content from {url}")
            return []
        
        return self._extract_data_from_selectors(soup)
    
    def _get_next_page_url(self, current_url: str, current_page: int) -> Optional[str]:
        """
        Get the URL for the next page based on the pagination configuration.
        
        Args:
            current_url: The URL of the current page
            current_page: The current page number (1-indexed)
            
        Returns:
            Optional[str]: The URL of the next page, or None if there is no next page
        """
        if not self.pagination:
            return None
        
        if self.pagination.type == PaginationType.URL_PARAM:
            return self._get_next_page_url_param(current_url, current_page)
        elif self.pagination.type == PaginationType.NEXT_BUTTON:
            return self._get_next_page_url_button(current_url)
        elif self.pagination.type == PaginationType.LOAD_MORE:
            # Load more button pagination is not supported by requests backend
            logger.warning("Load more button pagination is not supported by the requests backend")
            return None
        elif self.pagination.type == PaginationType.INFINITE_SCROLL:
            # Infinite scroll pagination is not supported by requests backend
            logger.warning("Infinite scroll pagination is not supported by the requests backend")
            return None
        
        return None
    
    def _get_next_page_url_param(self, current_url: str, current_page: int) -> Optional[str]:
        """
        Get the next page URL for URL parameter-based pagination.
        
        Args:
            current_url: The URL of the current page
            current_page: The current page number (1-indexed)
            
        Returns:
            Optional[str]: The URL of the next page
        """
        if not self.pagination or not self.pagination.param_name:
            return None
        
        # Parse the current URL
        parsed_url = urllib.parse.urlparse(current_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Update or add the page parameter
        param_name = self.pagination.param_name
        next_page = current_page + 1
        query_params[param_name] = [str(next_page)]
        
        # Rebuild the URL
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        new_url = urllib.parse.urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        return new_url
    
    def _get_next_page_url_button(self, current_url: str) -> Optional[str]:
        """
        Get the next page URL for button-based pagination.
        
        Args:
            current_url: The URL of the current page
            
        Returns:
            Optional[str]: The URL of the next page
        """
        if not self.pagination or not self.pagination.selector:
            return None
        
        # Get the current page content
        soup = self._get_page_content(current_url)
        if not soup:
            return None
        
        # Find the next button using the selector
        next_buttons = soup.select(self.pagination.selector)
        if not next_buttons or len(next_buttons) == 0:
            logger.debug(f"Next button not found with selector: {self.pagination.selector}")
            return None
        
        next_button = next_buttons[0]
        
        # Extract the URL from the button
        if next_button.name == "a" and next_button.get("href"):
            next_url = next_button["href"]
        else:
            # Try to find an anchor tag within the button
            anchor = next_button.find("a")
            if anchor and anchor.get("href"):
                next_url = anchor["href"]
            else:
                logger.debug("Next button found but no URL could be extracted")
                return None
        
        # Convert relative URL to absolute
        if next_url.startswith("/"):
            # Parse the current URL to get the base
            parsed_url = urllib.parse.urlparse(current_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            next_url = base_url + next_url
        elif not next_url.startswith(("http://", "https://")):
            # Handle other relative URLs
            next_url = urllib.parse.urljoin(current_url, next_url)
        
        return next_url 