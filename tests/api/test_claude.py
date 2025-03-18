"""
Tests for the Claude API client.
"""

import json
from typing import Any, Dict, TYPE_CHECKING
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError

from quickscrape.api.claude import ClaudeAPIClient, ClaudeConfig, ClaudeModel

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_httpx_client(monkeypatch: "MonkeyPatch") -> MagicMock:
    """
    Fixture that mocks the httpx.Client.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture.
        
    Returns:
        MagicMock for the httpx.Client.
    """
    mock_client = MagicMock()
    
    # Configure the mock client to properly handle close() method
    mock_client.close = MagicMock()
    
    # Mock the Client constructor to return our configured client
    mock_client_cls = MagicMock(return_value=mock_client)
    monkeypatch.setattr(httpx, "Client", mock_client_cls)
    
    return mock_client


@pytest.fixture
def claude_config() -> ClaudeConfig:
    """
    Fixture that returns a valid Claude API configuration.
    
    Returns:
        ClaudeConfig object with test values.
    """
    return ClaudeConfig(
        api_key="test_api_key",
        model=ClaudeModel.CLAUDE_3_HAIKU,
        max_tokens=100,
        temperature=0.0,
    )


@pytest.fixture
def claude_client(claude_config: ClaudeConfig, mock_httpx_client: MagicMock) -> ClaudeAPIClient:
    """
    Fixture that returns a Claude API client.
    
    Args:
        claude_config: Claude API configuration fixture.
        mock_httpx_client: Mock HTTP client.
        
    Returns:
        Configured ClaudeAPIClient.
    """
    return ClaudeAPIClient(config=claude_config)


class TestClaudeConfig:
    """Tests for the ClaudeConfig class."""
    
    def test_valid_config(self) -> None:
        """Test creating a valid configuration."""
        config = ClaudeConfig(
            api_key="test_api_key",
            model=ClaudeModel.CLAUDE_3_HAIKU,
            max_tokens=100,
            temperature=0.5,
        )
        
        assert config.api_key == "test_api_key"
        assert config.model == ClaudeModel.CLAUDE_3_HAIKU
        assert config.max_tokens == 100
        assert config.temperature == 0.5
    
    def test_invalid_temperature(self) -> None:
        """Test validation for temperature outside valid range."""
        with pytest.raises(ValidationError):
            ClaudeConfig(
                api_key="test_api_key",
                temperature=1.5,  # Invalid: greater than 1
            )
        
        with pytest.raises(ValidationError):
            ClaudeConfig(
                api_key="test_api_key",
                temperature=-0.1,  # Invalid: less than 0
            )
    
    def test_invalid_max_tokens(self) -> None:
        """Test validation for non-positive max_tokens."""
        with pytest.raises(ValidationError):
            ClaudeConfig(
                api_key="test_api_key",
                max_tokens=0,  # Invalid: must be positive
            )
        
        with pytest.raises(ValidationError):
            ClaudeConfig(
                api_key="test_api_key",
                max_tokens=-10,  # Invalid: must be positive
            )


class TestClaudeAPIClient:
    """Tests for the ClaudeAPIClient class."""
    
    def test_init_with_config(self, claude_config: ClaudeConfig) -> None:
        """Test initialization with a configuration object."""
        with patch('httpx.Client'):
            client = ClaudeAPIClient(config=claude_config)
            assert client.config == claude_config
    
    def test_init_with_api_key(self) -> None:
        """Test initialization with just an API key."""
        with patch('httpx.Client'):
            client = ClaudeAPIClient(api_key="test_api_key")
            assert client.config.api_key == "test_api_key"
            assert client.config.model == ClaudeModel.CLAUDE_3_HAIKU  # Default model
    
    def test_init_without_credentials(self) -> None:
        """Test that initialization fails without credentials."""
        with pytest.raises(ValueError, match="Either config or api_key must be provided"):
            ClaudeAPIClient()
    
    def test_prepare_message(self, claude_client: ClaudeAPIClient) -> None:
        """Test message preparation for API calls."""
        html = "<html><body><h1>Test</h1></body></html>"
        description = "The main heading"
        
        message = claude_client._prepare_message(html, description)
        
        assert message["model"] == ClaudeModel.CLAUDE_3_HAIKU
        assert message["max_tokens"] == 100
        assert message["temperature"] == 0.0
        assert len(message["messages"]) == 1
        assert message["messages"][0]["role"] == "user"
        assert html in message["messages"][0]["content"]
        assert description in message["messages"][0]["content"]
    
    def test_generate_selector_success(
        self, claude_client: ClaudeAPIClient, mock_httpx_client: MagicMock
    ) -> None:
        """Test successful selector generation."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "h1.title"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.post.return_value = mock_response
        
        selector = claude_client.generate_selector(
            html_content="<html><body><h1 class='title'>Test</h1></body></html>",
            description="The main heading with class 'title'",
        )
        
        assert selector == "h1.title"
        mock_httpx_client.post.assert_called_once()
    
    def test_generate_selector_error(
        self, claude_client: ClaudeAPIClient, mock_httpx_client: MagicMock
    ) -> None:
        """Test error handling in selector generation."""
        # Mock API error
        mock_http_error = httpx.RequestError("API connection failed", request=MagicMock())
        mock_httpx_client.post.side_effect = mock_http_error
        
        with pytest.raises(httpx.RequestError):
            claude_client.generate_selector(
                html_content="<html><body><h1>Test</h1></body></html>",
                description="The main heading",
            )
    
    def test_context_manager(
        self, mock_httpx_client: MagicMock
    ) -> None:
        """Test using the client as a context manager."""
        with patch('httpx.Client', return_value=mock_httpx_client):
            with ClaudeAPIClient(api_key="test_api_key") as client:
                pass
            
            mock_httpx_client.close.assert_called_once() 