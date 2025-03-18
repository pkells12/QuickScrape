"""
Tests for the requests-based scraper.
"""

from typing import Dict, List, Any, TYPE_CHECKING
from unittest.mock import patch, MagicMock, call

import pytest
from bs4 import BeautifulSoup

from quickscrape.config.models import (
    ScraperConfig,
    OutputConfig,
    OutputFormat,
    PaginationConfig,
    PaginationType,
)
from quickscrape.scraper.requests_scraper import RequestsScraper

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class MockResponse:
    """
    Mock response object for requests.
    """
    def __init__(self, text: str, url: str = "https://example.com", status_code: int = 200):
        """
        Initialize the mock response.
        
        Args:
            text: The response text
            url: The URL that was requested
            status_code: The HTTP status code
        """
        self.text = text
        self.url = url
        self.status_code = status_code
    
    def raise_for_status(self) -> None:
        """
        Raise an exception if the status code indicates an error.
        
        Returns:
            None
        """
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"Status code: {self.status_code}")


@pytest.fixture
def basic_config() -> ScraperConfig:
    """
    Fixture providing a basic scraper configuration.
    
    Returns:
        ScraperConfig: A basic configuration for testing
    """
    return ScraperConfig(
        url="https://example.com",
        selectors={"title": "h1", "content": "p.content"},
        output=OutputConfig(
            format=OutputFormat.CSV,
            path="output/test.csv"
        )
    )


@pytest.fixture
def config_with_pagination() -> ScraperConfig:
    """
    Fixture providing a scraper configuration with pagination.
    
    Returns:
        ScraperConfig: A configuration with pagination for testing
    """
    return ScraperConfig(
        url="https://example.com",
        selectors={"title": "h1", "content": "p.content"},
        pagination=PaginationConfig(
            type=PaginationType.URL_PARAM,
            param_name="page",
            max_pages=3
        ),
        output=OutputConfig(
            format=OutputFormat.CSV,
            path="output/test.csv"
        )
    )


@pytest.fixture
def sample_html() -> str:
    """
    Fixture providing sample HTML content.
    
    Returns:
        str: Sample HTML content for testing
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test Heading</h1>
        <p class="content">This is the main content.</p>
        <a href="https://example.com/next" class="next-page">Next Page</a>
    </body>
    </html>
    """


@pytest.fixture
def list_html() -> str:
    """
    Fixture providing HTML content with a list of items.
    
    Returns:
        str: Sample HTML content for testing list extraction
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
                <span class="price">$10.99</span>
            </li>
            <li class="product">
                <h2 class="product-title">Product 2</h2>
                <p class="product-desc">Description 2</p>
                <span class="price">$20.99</span>
            </li>
            <li class="product">
                <h2 class="product-title">Product 3</h2>
                <p class="product-desc">Description 3</p>
                <span class="price">$30.99</span>
            </li>
        </ul>
        <a href="https://example.com/?page=2" class="next-page">Next Page</a>
    </body>
    </html>
    """


def test_init_sets_headers():
    """
    Test that the initializer sets up default headers if none are provided.
    
    Returns:
        None
    """
    config = ScraperConfig(
        url="https://example.com",
        selectors={"title": "h1"},
        output=OutputConfig(format=OutputFormat.CSV, path="output.csv")
    )
    
    scraper = RequestsScraper(config)
    
    # Check that default headers were set
    assert "User-Agent" in scraper.headers
    assert "Accept" in scraper.headers
    assert "Accept-Language" in scraper.headers


@patch("requests.Session")
def test_before_scrape_setup_session(mock_session_class: MagicMock, basic_config: ScraperConfig) -> None:
    """
    Test that _before_scrape sets up the session correctly.
    
    Args:
        mock_session_class: Mocked requests.Session class
        basic_config: Basic scraper configuration
        
    Returns:
        None
    """
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    scraper = RequestsScraper(basic_config)
    scraper._before_scrape()
    
    assert scraper.session is not None
    mock_session_class.assert_called_once()
    
    # Check that headers were set on the session
    assert mock_session.headers.update.called


@patch("requests.Session")
def test_after_scrape_closes_session(mock_session_class: MagicMock, basic_config: ScraperConfig) -> None:
    """
    Test that _after_scrape closes the session.
    
    Args:
        mock_session_class: Mocked requests.Session class
        basic_config: Basic scraper configuration
        
    Returns:
        None
    """
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    scraper = RequestsScraper(basic_config)
    scraper._before_scrape()  # Set up the session
    scraper._after_scrape()   # Clean up
    
    # Check that session was closed
    mock_session.close.assert_called_once()
    assert scraper.session is None


def test_extract_value():
    """
    Test the _extract_value method for different HTML elements.
    
    Returns:
        None
    """
    scraper = RequestsScraper(
        ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1"},
            output=OutputConfig(format=OutputFormat.CSV, path="output.csv")
        )
    )
    
    # Test extracting from a link
    link = BeautifulSoup('<a href="https://example.com">Link Text</a>', "html.parser").a
    assert scraper._extract_value(link) == "https://example.com"
    
    # Test extracting from an image
    img = BeautifulSoup('<img src="image.jpg" alt="Alt Text">', "html.parser").img
    assert scraper._extract_value(img) == "image.jpg"
    
    # Test extracting from an input
    input_elem = BeautifulSoup('<input value="Input Value">', "html.parser").input
    assert scraper._extract_value(input_elem) == "Input Value"
    
    # Test extracting from a regular element
    p = BeautifulSoup('<p>Paragraph Text</p>', "html.parser").p
    assert scraper._extract_value(p) == "Paragraph Text"


@patch.object(RequestsScraper, "_get_page_content")
def test_scrape_page(mock_get_content: MagicMock, basic_config: ScraperConfig, sample_html: str) -> None:
    """
    Test the _scrape_page method.
    
    Args:
        mock_get_content: Mocked _get_page_content method
        basic_config: Basic scraper configuration
        sample_html: Sample HTML content
        
    Returns:
        None
    """
    mock_get_content.return_value = BeautifulSoup(sample_html, "html.parser")
    
    scraper = RequestsScraper(basic_config)
    result = scraper._scrape_page("https://example.com")
    
    # Check that _get_page_content was called
    mock_get_content.assert_called_once_with("https://example.com")
    
    # Check that data was extracted correctly
    assert len(result) == 1
    assert result[0]["title"] == "Test Heading"
    assert result[0]["content"] == "This is the main content."


@patch.object(RequestsScraper, "_get_page_content")
def test_scrape_page_list(
    mock_get_content: MagicMock, list_html: str
) -> None:
    """
    Test the _scrape_page method with list content.
    
    Args:
        mock_get_content: Mocked _get_page_content method
        list_html: Sample HTML with list content
        
    Returns:
        None
    """
    mock_get_content.return_value = BeautifulSoup(list_html, "html.parser")
    
    config = ScraperConfig(
        url="https://example.com",
        selectors={
            "title": ".product-title",
            "description": ".product-desc",
            "price": ".price"
        },
        output=OutputConfig(format=OutputFormat.CSV, path="output.csv")
    )
    
    scraper = RequestsScraper(config)
    result = scraper._scrape_page("https://example.com")
    
    # Check that list items were extracted correctly
    assert len(result) == 3
    assert result[0]["title"] == "Product 1"
    assert result[0]["description"] == "Description 1"
    assert result[0]["price"] == "$10.99"
    
    assert result[1]["title"] == "Product 2"
    assert result[2]["price"] == "$30.99"


def test_get_next_page_url_param(config_with_pagination: ScraperConfig) -> None:
    """
    Test the _get_next_page_url_param method.
    
    Args:
        config_with_pagination: Configuration with pagination settings
        
    Returns:
        None
    """
    scraper = RequestsScraper(config_with_pagination)
    
    # Test with URL without query parameters
    next_url = scraper._get_next_page_url_param("https://example.com", 1)
    assert next_url == "https://example.com?page=2"
    
    # Test with URL that already has the query parameter
    next_url = scraper._get_next_page_url_param("https://example.com?page=2", 2)
    assert next_url == "https://example.com?page=3"
    
    # Test with URL that has other query parameters
    next_url = scraper._get_next_page_url_param("https://example.com?sort=asc&page=1", 1)
    assert "sort=asc" in next_url
    assert "page=2" in next_url


@patch.object(RequestsScraper, "_get_page_content")
def test_get_next_page_url_button(
    mock_get_content: MagicMock,
    sample_html: str
) -> None:
    """
    Test the _get_next_page_url_button method.
    
    Args:
        mock_get_content: Mocked _get_page_content method
        sample_html: Sample HTML content
        
    Returns:
        None
    """
    mock_get_content.return_value = BeautifulSoup(sample_html, "html.parser")
    
    config = ScraperConfig(
        url="https://example.com",
        selectors={"title": "h1"},
        pagination=PaginationConfig(
            type=PaginationType.NEXT_BUTTON,
            selector=".next-page"
        ),
        output=OutputConfig(format=OutputFormat.CSV, path="output.csv")
    )
    
    scraper = RequestsScraper(config)
    next_url = scraper._get_next_page_url_button("https://example.com")
    
    # Check that _get_page_content was called
    mock_get_content.assert_called_once_with("https://example.com")
    
    # Check that the next URL was extracted correctly
    assert next_url == "https://example.com/next"


@patch.object(RequestsScraper, "_get_page_content")
def test_get_next_page_url_button_not_found(
    mock_get_content: MagicMock,
    sample_html: str
) -> None:
    """
    Test the _get_next_page_url_button method when the button is not found.
    
    Args:
        mock_get_content: Mocked _get_page_content method
        sample_html: Sample HTML content
        
    Returns:
        None
    """
    mock_get_content.return_value = BeautifulSoup(sample_html, "html.parser")
    
    config = ScraperConfig(
        url="https://example.com",
        selectors={"title": "h1"},
        pagination=PaginationConfig(
            type=PaginationType.NEXT_BUTTON,
            selector=".non-existent-button"  # This selector doesn't exist in the HTML
        ),
        output=OutputConfig(format=OutputFormat.CSV, path="output.csv")
    )
    
    scraper = RequestsScraper(config)
    next_url = scraper._get_next_page_url_button("https://example.com")
    
    # Check that _get_page_content was called
    mock_get_content.assert_called_once_with("https://example.com")
    
    # Check that no URL was found
    assert next_url is None 