"""
Playwright-based scraper implementation for QuickScrape.

This module provides a scraper implementation using the Playwright library,
which is suitable for dynamic websites with JavaScript requirements.
"""

import random
import time
import urllib.parse
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, AsyncGenerator

import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, Playwright, BrowserType
import nest_asyncio

from quickscrape.config.models import PaginationType
from quickscrape.scraper.base import BaseScraper
from quickscrape.utils.logger import get_logger

# Apply nest_asyncio to allow running asyncio in Jupyter/IPython environments
nest_asyncio.apply()
logger = get_logger(__name__)


class PlaywrightScraper(BaseScraper):
    """
    Scraper implementation using the Playwright library.
    
    This scraper is suitable for dynamic websites that require JavaScript
    execution. It uses Playwright for browser automation and BeautifulSoup
    for HTML parsing and selector processing.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the Playwright-based scraper.
        
        Args:
            *args: Positional arguments to pass to the parent constructor
            **kwargs: Keyword arguments to pass to the parent constructor
        """
        super().__init__(*args, **kwargs)
        
        # Playwright-specific settings
        self._browser_type = "chromium"  # Options: chromium, firefox, webkit
        self._headless = True
        self._slow_mo = 50 if self.random_delay else 0  # Slow down actions by 50ms
        
        # These will be set during _before_scrape
        self._playwright = None
        self._browser = None
        self._page = None
        
        # Advanced anti-bot options
        self.stealth_mode = True
        self.random_mouse_movements = True
    
    def _before_scrape(self) -> None:
        """
        Set up the Playwright browser before scraping begins.
        
        Launches a new browser instance and sets up the page with
        configured user agent and headers.
        """
        # Synchronously run the async setup
        asyncio.run(self._async_setup())
    
    async def _async_setup(self) -> None:
        """
        Asynchronously set up the Playwright browser.
        """
        self._playwright = await async_playwright().start()
        
        # Select browser type
        browser_type: BrowserType
        if self._browser_type == "firefox":
            browser_type = self._playwright.firefox
        elif self._browser_type == "webkit":
            browser_type = self._playwright.webkit
        else:
            browser_type = self._playwright.chromium
        
        # Launch browser with appropriate options
        self._browser = await browser_type.launch(
            headless=self._headless,
            slow_mo=self._slow_mo
        )
        
        # Create a new context with custom user agent if specified
        context_options = {}
        if self.user_agent:
            context_options["user_agent"] = self.user_agent
        
        # Add extra headers if specified
        extra_headers = self.headers.copy() if self.headers else {}
        if extra_headers:
            context_options["extra_http_headers"] = extra_headers
        
        # Create a browser context
        context = await self._browser.new_context(**context_options)
        
        # Enable stealth mode if requested
        if self.stealth_mode:
            await self._apply_stealth_mode(context)
        
        # Create a new page
        self._page = await context.new_page()
        
        logger.debug("Playwright browser setup completed")
    
    async def _apply_stealth_mode(self, context) -> None:
        """
        Apply stealth mode to avoid detection as a bot.
        
        Args:
            context: Playwright browser context
        """
        # These are simplified stealth measures - could be expanded with a more comprehensive set
        await context.add_init_script("""
        () => {
            // Override webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [1, 2, 3, 4, 5];
                }
            });
            
            // Override platform
            Object.defineProperty(navigator, 'platform', {
                get: () => {
                    return 'Win32';
                }
            });
            
            // Override ProductSub
            Object.defineProperty(navigator, 'productSub', {
                get: () => {
                    return '20100101';
                }
            });
        }
        """)
    
    def _after_scrape(self) -> None:
        """
        Clean up Playwright resources after scraping completes.
        """
        if self._browser:
            asyncio.run(self._async_cleanup())
    
    async def _async_cleanup(self) -> None:
        """
        Asynchronously clean up Playwright resources.
        """
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    async def _perform_random_mouse_movements(self, page: Page) -> None:
        """
        Perform random mouse movements to simulate human behavior.
        
        Args:
            page: Playwright page
        """
        # Define viewport dimensions
        viewport_size = await page.evaluate("""
            () => { 
                return { 
                    width: window.innerWidth, 
                    height: window.innerHeight 
                }; 
            }
        """)
        width = viewport_size["width"]
        height = viewport_size["height"]
        
        # Perform random mouse movements
        num_movements = random.randint(2, 5)
        for _ in range(num_movements):
            x = random.randint(0, width)
            y = random.randint(0, height)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def _scroll_page(self, page: Page) -> None:
        """
        Scroll the page to ensure all dynamic content is loaded.
        
        Args:
            page: Playwright page
        """
        # Get page height
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        
        # Scroll in increments
        current_position = 0
        while current_position < page_height:
            # Scroll down by viewport height
            current_position += viewport_height
            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Check if page height has increased due to dynamic loading
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > page_height:
                page_height = new_height
    
    async def _async_get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Asynchronously fetch and parse the page content.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Optional[BeautifulSoup]: Parsed HTML content, or None if the request failed
        """
        try:
            logger.debug(f"Navigating to URL: {url}")
            
            # Navigate to the URL with timeout
            response = await self._page.goto(url, timeout=60000, wait_until="networkidle")
            
            # Check if navigation was successful
            if not response:
                logger.error(f"Failed to navigate to {url}")
                return None
            
            if not response.ok:
                logger.error(f"HTTP error {response.status} for {url}")
                return None
            
            # Wait for content to load and render
            await self._page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1)  # Additional delay to ensure rendering
            
            # Scroll to load dynamic content if needed
            await self._scroll_page(self._page)
            
            # Perform random mouse movements if enabled
            if self.random_mouse_movements:
                await self._perform_random_mouse_movements(self._page)
            
            # Get the fully rendered HTML content
            content = await self._page.content()
            
            # Parse with BeautifulSoup
            return BeautifulSoup(content, "html.parser")
            
        except Exception as e:
            logger.error(f"Error accessing {url}: {str(e)}")
            return None
    
    async def _async_click_selector(self, selector: str) -> bool:
        """
        Asynchronously click an element using its selector.
        
        Args:
            selector: CSS selector for the element to click
            
        Returns:
            bool: True if the click was successful, False otherwise
        """
        try:
            # Ensure element is visible and wait for it
            await self._page.wait_for_selector(selector, state="visible", timeout=5000)
            
            # Scroll into view
            await self._page.evaluate(f"""
                (selector) => {{
                    const element = document.querySelector(selector);
                    if (element) element.scrollIntoView();
                }}
            """, selector)
            
            # Click the element
            await self._page.click(selector)
            
            # Wait for any network activity to settle
            await self._page.wait_for_load_state("networkidle")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clicking selector {selector}: {str(e)}")
            return False
    
    def _extract_data_from_selectors(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract data from the parsed HTML using the configured selectors.
        
        Args:
            soup: The parsed HTML content
            
        Returns:
            List[Dict[str, Any]]: List of extracted items
        """
        # This implementation is identical to the RequestsScraper version
        # Determine if we need to extract multiple items or just one
        items = []
        single_item = {}
        needs_list_extraction = False
        
        # Check if multiple elements match each selector
        selector_counts = {}
        for field, selector in self.selectors.items():
            elements = soup.select(selector)
            selector_counts[field] = len(elements)
        
        # If any selector has multiple matches, we need list extraction
        needs_list_extraction = any(count > 1 for count in selector_counts.values())
        
        if needs_list_extraction:
            # Try to find a common container and item selector
            common_containers = [
                ("ul", "li"),
                ("ol", "li"),
                ("table", "tr"),
                ("div.products", "div.product"),
                ("div.items", "div.item"),
                ("div.results", "div.result"),
                ("div.listing", "div.listing-item"),
            ]
            
            container_selector = None
            item_selector = None
            
            for container_tag, item_tag in common_containers:
                container = soup.select_first(container_tag)
                if container and container.select(item_tag):
                    container_selector = container_tag
                    item_selector = item_tag
                    break
            
            if container_selector and item_selector:
                container = soup.select_first(container_selector)
                if container:
                    item_elements = container.select(item_selector)
                    
                    for item_element in item_elements:
                        item_data = {}
                        for field, selector in self.selectors.items():
                            # Try to find elements within this item context
                            found = item_element.select(selector)
                            if found:
                                # Extract text or attribute depending on element type
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
                    # Extract text or attribute depending on element type
                    single_item[field] = self._extract_value(elements[0])
            
            if single_item:
                items.append(single_item)
        
        return items
    
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
        # Run the async scraping function synchronously
        return asyncio.run(self._async_scrape_page(url))
    
    async def _async_scrape_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Asynchronously scrape a single page and extract data.
        
        Args:
            url: The URL of the page to scrape
            
        Returns:
            List[Dict[str, Any]]: List of extracted items
        """
        soup = await self._async_get_page_content(url)
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
        # Run the async pagination function synchronously
        return asyncio.run(self._async_get_next_page_url(current_url, current_page))
    
    async def _async_get_next_page_url(self, current_url: str, current_page: int) -> Optional[str]:
        """
        Asynchronously get the URL for the next page.
        
        Args:
            current_url: The URL of the current page
            current_page: The current page number (1-indexed)
            
        Returns:
            Optional[str]: The URL of the next page, or None if there is no next page
        """
        if not self.pagination:
            return None
        
        if self.pagination.type == PaginationType.URL_PARAM:
            # URL parameter-based pagination (same as RequestsScraper)
            if not self.pagination.param_name:
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
            
        elif self.pagination.type == PaginationType.NEXT_BUTTON:
            # Button-based pagination
            if not self.pagination.selector:
                return None
            
            # Try to click the next button
            clicked = await self._async_click_selector(self.pagination.selector)
            
            if clicked:
                # Return the current URL after clicking (it may have changed)
                return await self._page.url()
            else:
                return None
                
        elif self.pagination.type == PaginationType.LOAD_MORE:
            # Load more button pagination
            if not self.pagination.selector:
                return None
            
            # Try to click the load more button
            clicked = await self._async_click_selector(self.pagination.selector)
            
            if clicked:
                # For load more, we return the same URL since we're still on the same page
                # The _scrape_page method will get the updated content
                await asyncio.sleep(2)  # Wait for content to load
                return current_url
            else:
                return None
                
        elif self.pagination.type == PaginationType.INFINITE_SCROLL:
            # Infinite scroll pagination
            # Simulate scrolling to the bottom
            await self._page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
            """)
            
            # Wait for any dynamic content to load
            await asyncio.sleep(2)
            await self._page.wait_for_load_state("networkidle")
            
            # Check if more content was loaded
            old_height = await self._page.evaluate("document.body.scrollHeight")
            await self._page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
            """)
            await asyncio.sleep(1)
            new_height = await self._page.evaluate("document.body.scrollHeight")
            
            if new_height > old_height:
                # More content was loaded, return the same URL to process it
                return current_url
            else:
                # No more content to load
                return None
        
        return None 