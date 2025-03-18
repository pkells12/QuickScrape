"""
Tests for the scraper factory module.
"""

from typing import Dict, TYPE_CHECKING
from unittest.mock import patch, MagicMock

import pytest
from bs4 import BeautifulSoup

from quickscrape.config.models import BackendType, ScraperConfig, OutputConfig, OutputFormat
from quickscrape.scraper.factory import (
    create_scraper,
    auto_detect_backend,
    _check_if_needs_javascript
)
from quickscrape.scraper.requests_scraper import RequestsScraper
from quickscrape.scraper.playwright_scraper import PlaywrightScraper

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def sample_config() -> ScraperConfig:
    """
    Fixture providing a sample scraper configuration.
    
    Returns:
        ScraperConfig: A sample configuration for testing
    """
    return ScraperConfig(
        url="https://example.com",
        selectors={"title": "h1", "content": "p"},
        output=OutputConfig(
            format=OutputFormat.CSV,
            path="output/test.csv"
        )
    )


@pytest.fixture
def static_html() -> str:
    """
    Fixture providing HTML content for a static page.
    
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
        <h1>Test Heading</h1>
        <p>This is a static page with no JavaScript dependencies.</p>
        <div class="content">
            <p>More content here.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def js_heavy_html() -> str:
    """
    Fixture providing HTML content for a JavaScript-heavy page.
    
    Returns:
        str: Sample HTML content
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test JS Page</title>
        <script src="https://cdn.jsdelivr.net/npm/react@17/umd/react.production.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/react-dom@17/umd/react-dom.production.min.js"></script>
    </head>
    <body>
        <div id="root"></div>
        <script>
            const app = React.createElement('div', null, 'Hello from React');
            ReactDOM.render(app, document.getElementById('root'));
        </script>
        <div class="loading-spinner"></div>
    </body>
    </html>
    """


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


def test_create_scraper_with_explicit_backend(sample_config: ScraperConfig) -> None:
    """
    Test creating a scraper with an explicitly specified backend.
    
    Args:
        sample_config: Sample scraper configuration
        
    Returns:
        None
    """
    # Test with explicitly set REQUESTS backend
    sample_config.backend = BackendType.REQUESTS
    scraper = create_scraper(sample_config)
    assert isinstance(scraper, RequestsScraper)
    
    # Test with explicitly set PLAYWRIGHT backend
    sample_config.backend = BackendType.PLAYWRIGHT
    scraper = create_scraper(sample_config)
    assert isinstance(scraper, PlaywrightScraper)


@patch("quickscrape.scraper.factory.auto_detect_backend")
def test_create_scraper_with_auto_detection(
    mock_auto_detect: MagicMock, sample_config: ScraperConfig
) -> None:
    """
    Test creating a scraper with automatic backend detection.
    
    Args:
        mock_auto_detect: Mocked auto_detect_backend function
        sample_config: Sample scraper configuration
        
    Returns:
        None
    """
    # Test auto-detection returning REQUESTS
    mock_auto_detect.return_value = BackendType.REQUESTS
    sample_config.backend = BackendType.AUTO
    
    scraper = create_scraper(sample_config)
    assert isinstance(scraper, RequestsScraper)
    mock_auto_detect.assert_called_once_with(sample_config)
    
    # Reset the mock and test auto-detection returning PLAYWRIGHT
    mock_auto_detect.reset_mock()
    mock_auto_detect.return_value = BackendType.PLAYWRIGHT
    
    scraper = create_scraper(sample_config)
    assert isinstance(scraper, PlaywrightScraper)
    mock_auto_detect.assert_called_once_with(sample_config)


@patch("requests.get")
def test_auto_detect_backend_static_page(
    mock_get: MagicMock, sample_config: ScraperConfig, static_html: str
) -> None:
    """
    Test auto-detection with a static page.
    
    Args:
        mock_get: Mocked requests.get function
        sample_config: Sample scraper configuration
        static_html: Sample static HTML content
        
    Returns:
        None
    """
    mock_get.return_value = MockResponse(static_html)
    
    backend = auto_detect_backend(sample_config)
    assert backend == BackendType.REQUESTS
    mock_get.assert_called_once()


@patch("requests.get")
def test_auto_detect_backend_js_page(
    mock_get: MagicMock, sample_config: ScraperConfig, js_heavy_html: str
) -> None:
    """
    Test auto-detection with a JavaScript-heavy page.
    
    Args:
        mock_get: Mocked requests.get function
        sample_config: Sample scraper configuration
        js_heavy_html: Sample JavaScript-heavy HTML content
        
    Returns:
        None
    """
    mock_get.return_value = MockResponse(js_heavy_html)
    
    backend = auto_detect_backend(sample_config)
    assert backend == BackendType.PLAYWRIGHT
    mock_get.assert_called_once()


@patch("requests.get")
def test_auto_detect_backend_request_error(
    mock_get: MagicMock, sample_config: ScraperConfig
) -> None:
    """
    Test auto-detection when the request fails.
    
    Args:
        mock_get: Mocked requests.get function
        sample_config: Sample scraper configuration
        
    Returns:
        None
    """
    # Simulate a request error
    mock_get.side_effect = Exception("Connection error")
    
    # Should default to Playwright when detection fails
    backend = auto_detect_backend(sample_config)
    assert backend == BackendType.PLAYWRIGHT
    mock_get.assert_called_once()


def test_check_if_needs_javascript(static_html: str, js_heavy_html: str) -> None:
    """
    Test the JavaScript detection logic.
    
    Args:
        static_html: Sample static HTML content
        js_heavy_html: Sample JavaScript-heavy HTML content
        
    Returns:
        None
    """
    static_soup = BeautifulSoup(static_html, "html.parser")
    js_soup = BeautifulSoup(js_heavy_html, "html.parser")
    
    # Static page should not need JavaScript
    assert not _check_if_needs_javascript(static_soup, "https://example.com")
    
    # JS-heavy page should need JavaScript
    assert _check_if_needs_javascript(js_soup, "https://example.com") 