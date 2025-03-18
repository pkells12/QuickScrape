"""
Tests for the selector generator.
"""

import os
from typing import Dict, Optional, TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from quickscrape.api.claude import ClaudeAPIClient
from quickscrape.api.selector_generator import SelectorGenerator
from quickscrape.config.models import ScraperConfig, OutputFormat
from quickscrape.scraper.factory import create_scraper

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_env_api_key(monkeypatch: "MonkeyPatch") -> None:
    """
    Fixture that sets a mock Claude API key in the environment.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    monkeypatch.setenv("CLAUDE_API_KEY", "test_env_api_key")


@pytest.fixture
def selector_generator() -> SelectorGenerator:
    """
    Fixture that returns a selector generator with a direct API key.
    
    Returns:
        Configured SelectorGenerator.
    """
    return SelectorGenerator(api_key="test_api_key")


@pytest.fixture
def sample_config() -> ScraperConfig:
    """
    Fixture that returns a sample scraper configuration with selector descriptions.
    
    Returns:
        Sample ScraperConfig object.
    """
    return ScraperConfig(
        url="https://example.com",
        selectors={},  # Empty selectors to be filled by generator
        selector_descriptions={
            "title": "The main page title",
            "price": "The product price including currency symbol",
            "description": "The product description paragraphs",
        },
        output={
            "format": OutputFormat.CSV,
            "path": "output.csv",
        },
    )


class TestSelectorGenerator:
    """Tests for the SelectorGenerator class."""
    
    def test_init_with_api_key(self) -> None:
        """Test initialization with a direct API key."""
        generator = SelectorGenerator(api_key="test_api_key")
        assert generator.api_key == "test_api_key"
        assert generator.claude_config.api_key == "test_api_key"
    
    def test_init_with_env_api_key(self, mock_env_api_key: None) -> None:
        """Test initialization using API key from environment."""
        generator = SelectorGenerator()
        assert generator.api_key == "test_env_api_key"
        assert generator.claude_config.api_key == "test_env_api_key"
    
    def test_init_without_api_key(self, monkeypatch: "MonkeyPatch") -> None:
        """Test that initialization fails without an API key."""
        # Ensure environment variable is not set
        monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="Claude API key must be provided"):
            SelectorGenerator()
    
    @patch("quickscrape.api.selector_generator.create_scraper")
    @patch("quickscrape.api.selector_generator.ClaudeAPIClient")
    def test_generate_selectors(
        self,
        mock_claude_client_cls: MagicMock,
        mock_create_scraper: MagicMock,
        selector_generator: SelectorGenerator,
        sample_config: ScraperConfig,
    ) -> None:
        """Test selector generation from descriptions."""
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_html.return_value = "<html><body><h1>Test Page</h1></body></html>"
        mock_create_scraper.return_value = mock_scraper
        
        # Mock Claude client
        mock_claude_client = MagicMock()
        mock_claude_client.generate_selectors_from_config.return_value = {
            "title": "h1",
            "price": ".price-tag",
            "description": "p.description",
        }
        mock_claude_client_cls.return_value.__enter__.return_value = mock_claude_client
        
        # Call the method
        selectors = selector_generator.generate_selectors(sample_config)
        
        # Assertions
        assert selectors == {
            "title": "h1",
            "price": ".price-tag",
            "description": "p.description",
        }
        mock_create_scraper.assert_called_once()
        mock_scraper.get_html.assert_called_once_with("https://example.com")
        mock_claude_client.generate_selectors_from_config.assert_called_once()
    
    def test_generate_selectors_without_descriptions(
        self, selector_generator: SelectorGenerator
    ) -> None:
        """Test that generating selectors fails without descriptions."""
        config = ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1"},  # Has selectors but no descriptions
            output={
                "format": OutputFormat.CSV,
                "path": "output.csv",
            },
        )
        
        with pytest.raises(ValueError, match="must contain selector_descriptions"):
            selector_generator.generate_selectors(config)
    
    @patch("quickscrape.api.selector_generator.create_scraper")
    @patch("quickscrape.api.selector_generator.ClaudeAPIClient")
    def test_update_config_with_selectors(
        self,
        mock_claude_client_cls: MagicMock,
        mock_create_scraper: MagicMock,
        selector_generator: SelectorGenerator,
        sample_config: ScraperConfig,
    ) -> None:
        """Test updating a config with generated selectors."""
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_html.return_value = "<html><body><h1>Test Page</h1></body></html>"
        mock_create_scraper.return_value = mock_scraper
        
        # Mock Claude client
        mock_claude_client = MagicMock()
        mock_claude_client.generate_selectors_from_config.return_value = {
            "title": "h1",
            "price": ".price-tag", 
            "description": "p.description",
        }
        mock_claude_client_cls.return_value.__enter__.return_value = mock_claude_client
        
        # Call the method
        updated_config = selector_generator.update_config_with_selectors(sample_config)
        
        # Assertions
        assert updated_config.selectors == {
            "title": "h1",
            "price": ".price-tag",
            "description": "p.description",
        }
        assert updated_config is not sample_config  # Should be a new instance
    
    @patch("quickscrape.api.selector_generator.create_scraper")
    @patch("quickscrape.api.selector_generator.ClaudeAPIClient")
    def test_interactive_selector_generation(
        self,
        mock_claude_client_cls: MagicMock,
        mock_create_scraper: MagicMock,
        selector_generator: SelectorGenerator,
    ) -> None:
        """Test interactive selector generation."""
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_html.return_value = "<html><body><h1>Test Page</h1></body></html>"
        mock_create_scraper.return_value = mock_scraper
        
        # Mock Claude client
        mock_claude_client = MagicMock()
        mock_claude_client.generate_selectors_from_config.return_value = {
            "title": "h1",
            "price": ".price-tag",
        }
        mock_claude_client_cls.return_value.__enter__.return_value = mock_claude_client
        
        # Call the method
        field_descriptions = {
            "title": "The main title",
            "price": "The product price",
        }
        selectors = selector_generator.interactive_selector_generation(
            "https://example.com", field_descriptions
        )
        
        # Assertions
        assert selectors == {
            "title": "h1",
            "price": ".price-tag",
        }
        mock_create_scraper.assert_called_once()
        mock_claude_client.generate_selectors_from_config.assert_called_once() 