"""Tests for the Playwright-based scraper."""

from unittest.mock import MagicMock, patch, AsyncMock
from typing import Any, Dict, Generator, Optional, TYPE_CHECKING

import pytest
from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import Page, Response as PlaywrightResponse, Browser

from quickscrape.config.models import (
    ScraperConfig, 
    OutputConfig, 
    OutputFormat, 
    PaginationConfig, 
    PaginationType,
    BackendType
)
from quickscrape.scraper.playwright_scraper import PlaywrightScraper

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def basic_config() -> ScraperConfig:
    """
    Provide a basic scraper configuration.
    
    Returns:
        ScraperConfig: A basic configuration for testing
    """
    return ScraperConfig(
        url="https://example.com",
        selectors={
            "title": "h1",
            "description": "p.description",
            "price": "span.price"
        },
        output=OutputConfig(format=OutputFormat.CSV, path="output.csv")
    )


@pytest.fixture
def config_with_pagination() -> ScraperConfig:
    """
    Provide a scraper configuration with pagination settings.
    
    Returns:
        ScraperConfig: A configuration with pagination for testing
    """
    return ScraperConfig(
        url="https://example.com",
        selectors={
            "title": "h1",
            "description": "p.description",
            "price": "span.price"
        },
        pagination=PaginationConfig(
            type=PaginationType.NEXT_BUTTON,
            selector=".next-page"
        ),
        output=OutputConfig(format=OutputFormat.CSV, path="output.csv")
    )


@pytest.fixture
def sample_html() -> str:
    """
    Provide sample HTML content for testing.
    
    Returns:
        str: Sample HTML content
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test Title</h1>
        <p class="description">Test description content.</p>
        <span class="price">$29.99</span>
        <a href="https://example.com/next" class="next-page">Next Page</a>
    </body>
    </html>
    """


@pytest.fixture
def list_html() -> str:
    """
    Provide sample HTML with list content for testing.
    
    Returns:
        str: Sample HTML with list content
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Product List</title>
    </head>
    <body>
        <h1>Product List</h1>
        <ul class="products">
            <li class="product">
                <h2 class="product-title">Product 1</h2>
                <p class="product-desc">Description 1</p>
                <span class="price">$19.99</span>
            </li>
            <li class="product">
                <h2 class="product-title">Product 2</h2>
                <p class="product-desc">Description 2</p>
                <span class="price">$29.99</span>
            </li>
            <li class="product">
                <h2 class="product-title">Product 3</h2>
                <p class="product-desc">Description 3</p>
                <span class="price">$39.99</span>
            </li>
        </ul>
        <a href="https://example.com/?page=2" class="next-page">Next Page</a>
    </body>
    </html>
    """


class MockPlaywrightResponse:
    """Mock response object for Playwright responses."""
    
    def __init__(self, status: int = 200, content: str = ""):
        """
        Initialize the mock response.
        
        Args:
            status: HTTP status code
            content: Response content
        """
        self.status = status
        self._content = content
        self.ok = status < 400
    
    async def text(self) -> str:
        """
        Get the response text.
        
        Returns:
            str: The response content
        """
        return self._content


@pytest.mark.asyncio
async def test_init_sets_correct_properties(basic_config: ScraperConfig) -> None:
    """
    Test that the initializer sets the correct properties.
    
    Args:
        basic_config: A basic scraper configuration
    
    Returns:
        None
    """
    scraper = PlaywrightScraper(basic_config)
    
    assert scraper.config == basic_config
    assert scraper.selectors == basic_config.selectors
    assert scraper.pagination == basic_config.pagination
    assert scraper._browser is None
    assert scraper._page is None


@pytest.mark.asyncio
async def test_async_setup(basic_config: ScraperConfig) -> None:
    """
    Test that _async_setup initializes the browser.
    
    Args:
        basic_config: A basic scraper configuration
    
    Returns:
        None
    """
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright_instance = AsyncMock()
        mock_browser_type = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        # Setup the mocks
        mock_playwright.return_value = mock_playwright_instance
        mock_playwright_instance.start = AsyncMock(return_value=mock_playwright_instance)
        mock_playwright_instance.chromium = mock_browser_type
        mock_browser_type.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        
        scraper = PlaywrightScraper(basic_config)
        
        await scraper._async_setup()
        
        # Assert that browser was launched with the correct options
        mock_browser_type.launch.assert_called_once()
        
        # Assert that the browser context and page were created
        mock_browser.new_context.assert_called_once()
        mock_context.new_page.assert_called_once()
        
        # Assert that the browser, context, and page are set
        assert scraper._browser is mock_browser
        assert scraper._page is mock_page


@pytest.mark.asyncio
async def test_async_cleanup(basic_config: ScraperConfig) -> None:
    """
    Test that _async_cleanup closes the browser.
    
    Args:
        basic_config: A basic scraper configuration
    
    Returns:
        None
    """
    scraper = PlaywrightScraper(basic_config)
    
    # Set up mock browser and playwright
    scraper._browser = AsyncMock()
    scraper._playwright = AsyncMock()
    
    await scraper._async_cleanup()
    
    # Assert that the browser and playwright were closed
    scraper._browser.close.assert_called_once()
    scraper._playwright.stop.assert_called_once()
    
    # Assert that the browser and playwright are set to None
    assert scraper._browser is None
    assert scraper._playwright is None


@pytest.mark.asyncio
async def test_async_get_page_content(basic_config: ScraperConfig, sample_html: str) -> None:
    """
    Test that _async_get_page_content correctly fetches and parses the page content.
    
    Args:
        basic_config: A basic scraper configuration
        sample_html: Sample HTML content
    
    Returns:
        None
    """
    scraper = PlaywrightScraper(basic_config)
    
    # Set up mock page
    scraper._page = AsyncMock()
    mock_response = MockPlaywrightResponse(200)
    scraper._page.goto = AsyncMock(return_value=mock_response)
    scraper._page.content = AsyncMock(return_value=sample_html)
    
    # Call the method and get the result
    result = await scraper._async_get_page_content("https://example.com")
    
    # Assert that the page was navigated to
    scraper._page.goto.assert_called_once_with("https://example.com", timeout=60000, wait_until="networkidle")
    
    # Assert that the page content was requested
    scraper._page.content.assert_called_once()
    
    # Assert that the result is a BeautifulSoup object with the correct content
    assert isinstance(result, BeautifulSoup)
    assert result.find("h1").text == "Test Title"
    assert result.find("p", class_="description").text == "Test description content."
    assert result.find("span", class_="price").text == "$29.99"


@pytest.mark.asyncio
async def test_extract_value(basic_config: ScraperConfig) -> None:
    """
    Test the _extract_value method with different HTML elements.
    
    Args:
        basic_config: A basic scraper configuration
    
    Returns:
        None
    """
    scraper = PlaywrightScraper(basic_config)
    
    # Test with a link element
    link = BeautifulSoup('<a href="https://example.com">Example</a>', "html.parser").a
    assert scraper._extract_value(link) == "https://example.com"
    
    # Test with an image element
    img = BeautifulSoup('<img src="image.jpg" alt="Alt Text">', "html.parser").img
    assert scraper._extract_value(img) == "image.jpg"
    
    # Test with an image element without src but with alt
    img_no_src = BeautifulSoup('<img alt="Alt Text">', "html.parser").img
    assert scraper._extract_value(img_no_src) == "Alt Text"
    
    # Test with an input element
    input_elem = BeautifulSoup('<input type="text" value="Input Value">', "html.parser").input
    assert scraper._extract_value(input_elem) == "Input Value"
    
    # Test with a regular element
    p = BeautifulSoup('<p>Paragraph Text</p>', "html.parser").p
    assert scraper._extract_value(p) == "Paragraph Text"


@pytest.mark.asyncio
async def test_scroll_page(basic_config: ScraperConfig) -> None:
    """
    Test the _scroll_page method.
    
    Args:
        basic_config: A basic scraper configuration
    
    Returns:
        None
    """
    scraper = PlaywrightScraper(basic_config)
    
    # Set up mock page
    page = AsyncMock()
    # Mock the page.evaluate to return fixed values for testing
    page.evaluate.side_effect = [
        # First call for document.body.scrollHeight
        1000,
        # Second call for window.innerHeight
        500,
        # Third call for window.scrollTo
        None,
        # Fourth call for document.body.scrollHeight (page height check)
        1200,
        # Fifth call for window.scrollTo
        None,
        # Sixth call for document.body.scrollHeight (page height check)
        1200,
        # Seventh call for window.scrollTo
        None
    ]
    
    # Call the method
    await scraper._scroll_page(page)
    
    # Assert that page.evaluate was called to perform scrolling
    assert page.evaluate.call_count >= 5


@pytest.mark.asyncio
async def test_async_click_selector(basic_config: ScraperConfig) -> None:
    """
    Test the _async_click_selector method.
    
    Args:
        basic_config: A basic scraper configuration
    
    Returns:
        None
    """
    scraper = PlaywrightScraper(basic_config)
    
    # Set up mock page
    scraper._page = AsyncMock()
    scraper._page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    scraper._page.click = AsyncMock()
    
    # Call the method
    result = await scraper._async_click_selector(".load-more-btn")
    
    # Assert that wait_for_selector and click were called
    scraper._page.wait_for_selector.assert_called_once_with(".load-more-btn", state="visible", timeout=10000)
    scraper._page.click.assert_called_once_with(".load-more-btn")
    assert result is True


@pytest.mark.asyncio
async def test_async_get_next_page_url(config_with_pagination: ScraperConfig, sample_html: str) -> None:
    """
    Test the _async_get_next_page_url method.
    
    Args:
        config_with_pagination: A scraper configuration with pagination
        sample_html: Sample HTML content
    
    Returns:
        None
    """
    scraper = PlaywrightScraper(config_with_pagination)
    
    # Set up mock page and patch the _async_get_page_content method
    with patch.object(
        PlaywrightScraper, 
        '_async_get_page_content', 
        return_value=BeautifulSoup(sample_html, "html.parser")
    ):
        # Call the method
        next_url = await scraper._async_get_next_page_url("https://example.com", 1)
        
        # Assert that the next URL is correct
        assert next_url == "https://example.com/next"


@pytest.mark.asyncio
async def test_async_scrape_page(basic_config: ScraperConfig, sample_html: str) -> None:
    """
    Test the _async_scrape_page method.
    
    Args:
        basic_config: A basic scraper configuration
        sample_html: Sample HTML content
    
    Returns:
        None
    """
    scraper = PlaywrightScraper(basic_config)
    
    # Patch the _async_get_page_content method
    with patch.object(
        PlaywrightScraper, 
        '_async_get_page_content', 
        return_value=BeautifulSoup(sample_html, "html.parser")
    ):
        # Call the method
        results = await scraper._async_scrape_page("https://example.com")
        
        # Assert that the results are as expected
        assert len(results) == 1
        assert results[0]["title"] == "Test Title"
        assert results[0]["description"] == "Test description content."
        assert results[0]["price"] == "$29.99"


@pytest.mark.asyncio
async def test_scrape_with_pagination(basic_config: ScraperConfig) -> None:
    """
    Test the scrape method with pagination.
    
    Args:
        basic_config: A basic scraper configuration
    
    Returns:
        None
    """
    # Create config with pagination
    config = ScraperConfig(
        url="https://example.com",
        selectors={"title": "h1"},
        pagination=PaginationConfig(
            type=PaginationType.NEXT_BUTTON,
            selector=".next-page",
            max_pages=2
        ),
        output=OutputConfig(format=OutputFormat.CSV, path="output.csv")
    )
    
    # Create a scraper with the mocked methods
    scraper = PlaywrightScraper(config)
    
    # Mock the required methods
    scraper._before_scrape = MagicMock()
    scraper._after_scrape = MagicMock()
    scraper._scrape_page = MagicMock(return_value=[{"title": "Test Title"}])
    scraper._get_next_page_url = MagicMock(side_effect=["https://example.com/page/2", None])
    
    # Call the scrape method
    results = scraper.scrape()
    
    # Assert that the required methods were called
    scraper._before_scrape.assert_called_once()
    assert scraper._scrape_page.call_count == 2
    scraper._after_scrape.assert_called_once()
    
    # Assert that the results are combined from both pages
    assert len(results) == 2
    assert results[0]["title"] == "Test Title"
    assert results[1]["title"] == "Test Title" 