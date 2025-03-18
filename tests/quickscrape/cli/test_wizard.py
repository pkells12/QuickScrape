"""
Tests for the terminal-based setup wizard.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup
from pydantic import ValidationError

from quickscrape.cli.wizard import (
    run_wizard,
    _prompt_for_config_name,
    _prompt_for_url,
    _prompt_for_selectors,
    _prompt_for_pagination,
    _prompt_for_output,
    _prompt_for_backend,
    _prompt_for_advanced_options,
)
from quickscrape.config.models import BackendType, OutputFormat, PaginationType

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class MockResponse:
    """
    A simple mock for requests.Response objects.
    """
    def __init__(self, text: str, status_code: int = 200) -> None:
        """
        Initialize a mock response.

        Args:
            text: The HTML content of the response
            status_code: The HTTP status code of the response
        """
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        """
        Raise an exception if the status code indicates an error.
        
        Returns:
            None
        
        Raises:
            requests.exceptions.HTTPError: If the status code is 4xx or 5xx
        """
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"Status code: {self.status_code}")


def mock_inquirer_prompt(questions: list) -> Dict[str, Any]:
    """
    Mock for inquirer.prompt function.

    Args:
        questions: List of inquirer question objects

    Returns:
        Dict[str, Any]: Mock answers
    """
    # Return a default answer based on the question type
    result = {}
    for q in questions:
        if hasattr(q, "name"):
            if q.name == "config_name":
                result[q.name] = "test_config"
            elif q.name == "url":
                result[q.name] = "https://example.com"
            elif q.name == "field_name":
                result[q.name] = "title"
            elif q.name == "selector":
                result[q.name] = "h1.title"
            elif q.name == "pagination_type":
                result[q.name] = PaginationType.URL_PARAM
            elif q.name == "param_name":
                result[q.name] = "page"
            elif q.name == "max_pages":
                result[q.name] = "5"
            elif q.name == "format":
                result[q.name] = OutputFormat.CSV
            elif q.name == "path":
                result[q.name] = "output/test.csv"
            elif q.name == "delimiter":
                result[q.name] = ","
            elif q.name == "backend":
                result[q.name] = BackendType.AUTO
            elif q.name == "wait_time":
                result[q.name] = "0.5"
            elif q.name == "user_agent":
                result[q.name] = "Mozilla/5.0"
            elif q.name == "header_name":
                result[q.name] = "Accept"
            elif q.name == "header_value":
                result[q.name] = "application/json"
    return result


def mock_inquirer_confirm(message: str, default: bool = False) -> bool:
    """
    Mock for inquirer.confirm function.

    Args:
        message: The confirmation message
        default: The default answer if none is provided

    Returns:
        bool: Always False for "Add another field?" and "Add another header?",
              otherwise True
    """
    if "another field" in message or "another header" in message:
        return False
    return True


@pytest.fixture
def mock_html_content() -> str:
    """
    Fixture providing a simple HTML content for testing.

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
        <h1 class="main-title">Test Page Title</h1>
        <div class="content">
            <p>This is a test paragraph.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_requests_get(mock_html_content: str) -> MagicMock:
    """
    Fixture for mocking requests.get.

    Args:
        mock_html_content: Sample HTML content to return

    Returns:
        MagicMock: Mocked requests.get function
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(mock_html_content)
        yield mock_get


@pytest.fixture
def mock_config_manager() -> MagicMock:
    """
    Fixture for mocking the config_manager module.

    Returns:
        MagicMock: Mocked config_manager module
    """
    with patch("quickscrape.cli.wizard.config_manager") as mock_cm:
        mock_cm.config_exists.return_value = False
        mock_cm.save_config.return_value = None
        yield mock_cm


@pytest.mark.parametrize(
    "func_name,expected_return_type",
    [
        ("_prompt_for_config_name", str),
        ("_prompt_for_url", str),
        ("_prompt_for_selectors", dict),
        ("_prompt_for_pagination", (dict, type(None))),
        ("_prompt_for_output", dict),
        ("_prompt_for_backend", str),
    ],
)
def test_prompt_functions(
    func_name: str,
    expected_return_type: Any,
    mock_requests_get: MagicMock,
    mock_config_manager: MagicMock,
) -> None:
    """
    Test individual prompt functions.

    Args:
        func_name: Name of the function to test
        expected_return_type: Expected return type of the function
        mock_requests_get: Mocked requests.get function
        mock_config_manager: Mocked config_manager module

    Returns:
        None
    """
    with patch("inquirer.prompt", side_effect=mock_inquirer_prompt), patch(
        "inquirer.confirm", side_effect=mock_inquirer_confirm
    ):
        func = globals()[func_name]
        if func_name == "_prompt_for_selectors":
            result = func("https://example.com")
        elif func_name == "_prompt_for_output":
            result = func("test_config")
        else:
            result = func()

        if isinstance(expected_return_type, tuple):
            assert any(isinstance(result, t) for t in expected_return_type)
        else:
            assert isinstance(result, expected_return_type)


def test_run_wizard(
    mock_requests_get: MagicMock,
    mock_config_manager: MagicMock,
    capsys: "CaptureFixture[str]",
) -> None:
    """
    Test the main run_wizard function.

    Args:
        mock_requests_get: Mocked requests.get function
        mock_config_manager: Mocked config_manager module
        capsys: Pytest fixture for capturing stdout/stderr

    Returns:
        None
    """
    with patch("inquirer.prompt", side_effect=mock_inquirer_prompt), patch(
        "inquirer.confirm", side_effect=mock_inquirer_confirm
    ), patch("sys.exit") as mock_exit:
        run_wizard("test_config")
        
        # Verify that config_manager.save_config was called
        mock_config_manager.save_config.assert_called_once()
        
        # Check that the function completed without exiting
        mock_exit.assert_not_called()
        
        # Check output
        captured = capsys.readouterr()
        assert "created successfully" in captured.out


def test_wizard_with_exception(
    mock_requests_get: MagicMock,
    mock_config_manager: MagicMock,
    capsys: "CaptureFixture[str]",
) -> None:
    """
    Test the wizard when a validation error occurs.

    Args:
        mock_requests_get: Mocked requests.get function
        mock_config_manager: Mocked config_manager module
        capsys: Pytest fixture for capturing stdout/stderr

    Returns:
        None
    """
    with patch("inquirer.prompt", side_effect=mock_inquirer_prompt), patch(
        "inquirer.confirm", side_effect=mock_inquirer_confirm
    ), patch("sys.exit") as mock_exit, patch(
        "quickscrape.cli.wizard.ScraperConfig", side_effect=ValidationError([{"loc": ("url",), "msg": "Invalid URL"}], ScraperConfig)
    ):
        run_wizard("test_config")
        
        # Check that config_manager.save_config was not called due to the error
        mock_config_manager.save_config.assert_not_called()
        
        # Check output
        captured = capsys.readouterr()
        assert "Error creating configuration" in captured.out 