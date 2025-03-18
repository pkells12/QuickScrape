"""Tests for the data extraction module."""

import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import pytest
from bs4 import BeautifulSoup

from quickscrape.data.extraction import (
    SelectorType,
    ExtractorConfig,
    CssExtractor,
    XPathExtractor,
    RegexExtractor,
    DataExtractor,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def sample_html() -> str:
    """Provide a sample HTML document for testing extractors.
    
    Returns:
        Sample HTML string
    """
    return """<!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1 class="main-title">Sample Page Title</h1>
        <div class="container">
            <p class="desc">This is a description.</p>
            <div class="product">
                <h2 class="product-title">Product 1</h2>
                <p class="price" data-value="19.99">$19.99</p>
                <p class="stock" data-in-stock="yes">In Stock</p>
                <div class="details">
                    <span class="feature">Feature 1</span>
                    <span class="feature">Feature 2</span>
                    <span class="feature">Feature 3</span>
                </div>
                <div class="metadata">
                    <span data-category="electronics">Category: Electronics</span>
                    <span data-rating="4.5">Rating: 4.5/5</span>
                </div>
            </div>
            <div class="product">
                <h2 class="product-title">Product 2</h2>
                <p class="price" data-value="29.99">$29.99</p>
                <p class="stock" data-in-stock="no">Out of Stock</p>
                <div class="details">
                    <span class="feature">Feature A</span>
                    <span class="feature">Feature B</span>
                </div>
                <div class="metadata">
                    <span data-category="home">Category: Home</span>
                    <span data-rating="3.8">Rating: 3.8/5</span>
                </div>
            </div>
        </div>
    </body>
    </html>"""


@pytest.fixture
def sample_soup(sample_html: str) -> BeautifulSoup:
    """Create a BeautifulSoup object from the sample HTML.
    
    Args:
        sample_html: Sample HTML string
        
    Returns:
        BeautifulSoup object
    """
    return BeautifulSoup(sample_html, "html.parser")


class TestCssExtractor:
    """Tests for the CSS selector-based extractor."""

    def test_simple_text_extraction(self, sample_soup: BeautifulSoup) -> None:
        """Test extraction of simple text using CSS selector.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        config: ExtractorConfig = {
            "selector": "h1.main-title",
            "selector_type": SelectorType.CSS
        }
        extractor = CssExtractor(config)
        result = extractor.extract(sample_soup)
        assert result == "Sample Page Title"

    def test_attribute_extraction(self, sample_soup: BeautifulSoup) -> None:
        """Test extraction of an attribute using CSS selector.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        config: ExtractorConfig = {
            "selector": "p.price",
            "selector_type": SelectorType.CSS,
            "attribute": "data-value"
        }
        extractor = CssExtractor(config)
        result = extractor.extract(sample_soup)
        assert result == "19.99"

    def test_multiple_elements(self, sample_soup: BeautifulSoup) -> None:
        """Test extraction of multiple elements using CSS selector.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        config: ExtractorConfig = {
            "selector": "span.feature",
            "selector_type": SelectorType.CSS,
            "multiple": True
        }
        extractor = CssExtractor(config)
        result = extractor.extract(sample_soup)
        assert isinstance(result, list)
        assert len(result) == 5
        assert "Feature 1" in result
        assert "Feature B" in result

    def test_extract_with_default(self, sample_soup: BeautifulSoup) -> None:
        """Test extraction with a default value for non-existent elements.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        config: ExtractorConfig = {
            "selector": "h3.non-existent",
            "selector_type": SelectorType.CSS,
            "default": "Not Found"
        }
        extractor = CssExtractor(config)
        result = extractor.extract(sample_soup)
        assert result == "Not Found"

    def test_transform_value(self, sample_soup: BeautifulSoup) -> None:
        """Test transformation of extracted value.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        config: ExtractorConfig = {
            "selector": "h1.main-title",
            "selector_type": SelectorType.CSS,
            "transform": "lower"
        }
        extractor = CssExtractor(config)
        result = extractor.extract(sample_soup)
        assert result == "sample page title"

    def test_regex_pattern(self, sample_soup: BeautifulSoup) -> None:
        """Test applying regex pattern to extracted text.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        config: ExtractorConfig = {
            "selector": "p.price",
            "selector_type": SelectorType.CSS,
            "regex_pattern": r"\$(\d+\.\d+)"
        }
        extractor = CssExtractor(config)
        result = extractor.extract(sample_soup)
        assert result == "19.99"
    
    def test_extract_from_string(self) -> None:
        """Test extraction from an HTML string instead of BeautifulSoup object."""
        html = "<div><span class='test'>Hello</span></div>"
        config: ExtractorConfig = {
            "selector": "span.test",
            "selector_type": SelectorType.CSS
        }
        extractor = CssExtractor(config)
        result = extractor.extract(html)
        assert result == "Hello"


class TestXPathExtractor:
    """Tests for the XPath selector-based extractor."""

    def test_simple_text_extraction(self, sample_soup: BeautifulSoup) -> None:
        """Test extraction of simple text using XPath.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        try:
            config: ExtractorConfig = {
                "selector": "//h1[@class='main-title']/text()",
                "selector_type": SelectorType.XPATH
            }
            extractor = XPathExtractor(config)
            result = extractor.extract(sample_soup)
            assert "Sample Page Title" in result
        except ImportError:
            pytest.skip("lxml not installed, skipping XPath tests")

    def test_attribute_extraction(self, sample_soup: BeautifulSoup) -> None:
        """Test extraction of an attribute using XPath.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        try:
            config: ExtractorConfig = {
                "selector": "//p[@class='price']/@data-value",
                "selector_type": SelectorType.XPATH
            }
            extractor = XPathExtractor(config)
            result = extractor.extract(sample_soup)
            assert result == "19.99"
        except ImportError:
            pytest.skip("lxml not installed, skipping XPath tests")

    def test_multiple_elements(self, sample_soup: BeautifulSoup) -> None:
        """Test extraction of multiple elements using XPath.
        
        Args:
            sample_soup: BeautifulSoup fixture
        """
        try:
            config: ExtractorConfig = {
                "selector": "//span[@class='feature']/text()",
                "selector_type": SelectorType.XPATH,
                "multiple": True
            }
            extractor = XPathExtractor(config)
            result = extractor.extract(sample_soup)
            assert isinstance(result, list)
            assert len(result) == 5
            assert "Feature 1" in result
            assert "Feature B" in result
        except ImportError:
            pytest.skip("lxml not installed, skipping XPath tests")


class TestRegexExtractor:
    """Tests for the regex-based extractor."""

    def test_simple_pattern(self, sample_html: str) -> None:
        """Test extraction using a simple regex pattern.
        
        Args:
            sample_html: Sample HTML string
        """
        config: ExtractorConfig = {
            "selector": r"<h1 class=\"main-title\">(.*?)<\/h1>",
            "selector_type": SelectorType.REGEX
        }
        extractor = RegexExtractor(config)
        result = extractor.extract(sample_html)
        assert result == "Sample Page Title"

    def test_multiple_matches(self, sample_html: str) -> None:
        """Test extraction of multiple matches using regex.
        
        Args:
            sample_html: Sample HTML string
        """
        config: ExtractorConfig = {
            "selector": r"<h2 class=\"product-title\">(.*?)<\/h2>",
            "selector_type": SelectorType.REGEX,
            "multiple": True
        }
        extractor = RegexExtractor(config)
        result = extractor.extract(sample_html)
        assert isinstance(result, list)
        assert len(result) == 2
        assert "Product 1" in result
        assert "Product 2" in result

    def test_capture_group(self, sample_html: str) -> None:
        """Test extraction with specific capture group.
        
        Args:
            sample_html: Sample HTML string
        """
        config: ExtractorConfig = {
            "selector": r"data-rating=\"([\d.]+)\">Rating: ([\d.]+)\/5",
            "selector_type": SelectorType.REGEX,
            "regex_group": 2  # Use the second capture group
        }
        extractor = RegexExtractor(config)
        result = extractor.extract(sample_html)
        assert result == "4.5"

    def test_no_match_with_default(self, sample_html: str) -> None:
        """Test extraction with no match but with default value.
        
        Args:
            sample_html: Sample HTML string
        """
        config: ExtractorConfig = {
            "selector": r"<nonexistent>(.*?)<\/nonexistent>",
            "selector_type": SelectorType.REGEX,
            "default": "No Match"
        }
        extractor = RegexExtractor(config)
        result = extractor.extract(sample_html)
        assert result == "No Match"
    
    def test_apply_secondary_regex(self, sample_html: str) -> None:
        """Test applying a secondary regex to the extracted value.
        
        Args:
            sample_html: Sample HTML string
        """
        config: ExtractorConfig = {
            "selector": r"data-rating=\"([\d.]+)\">Rating: [\d.]+\/5",
            "selector_type": SelectorType.REGEX,
            "regex_pattern": r"([\d.]+)",  # Extract just the number from the attribute
        }
        extractor = RegexExtractor(config)
        result = extractor.extract(sample_html)
        assert result == "4.5"


class TestDataExtractor:
    """Tests for the main DataExtractor class."""

    def test_extract_multiple_fields(self, sample_html: str) -> None:
        """Test extraction of multiple fields at once.
        
        Args:
            sample_html: Sample HTML string
        """
        extraction_config: Dict[str, ExtractorConfig] = {
            "title": {
                "selector": "h1.main-title",
                "selector_type": SelectorType.CSS
            },
            "products": {
                "selector": "h2.product-title",
                "selector_type": SelectorType.CSS,
                "multiple": True
            },
            "first_price": {
                "selector": "p.price",
                "selector_type": SelectorType.CSS,
                "attribute": "data-value"
            },
            "features": {
                "selector": "span.feature",
                "selector_type": SelectorType.CSS,
                "multiple": True
            }
        }
        
        extractor = DataExtractor(extraction_config)
        result = extractor.extract(sample_html)
        
        assert isinstance(result, dict)
        assert len(result) == 4
        assert result["title"] == "Sample Page Title"
        assert len(result["products"]) == 2
        assert result["first_price"] == "19.99"
        assert len(result["features"]) == 5

    def test_combined_selectors(self, sample_html: str) -> None:
        """Test using different selector types in the same extraction.
        
        Args:
            sample_html: Sample HTML string
        """
        try:
            # This will be skipped if lxml is not installed
            import lxml
            
            extraction_config: Dict[str, ExtractorConfig] = {
                "title": {
                    "selector": "h1.main-title",
                    "selector_type": SelectorType.CSS
                },
                "price_regex": {
                    "selector": r"\$(\d+\.\d+)",
                    "selector_type": SelectorType.REGEX,
                    "multiple": True
                },
                "categories": {
                    "selector": "//span[@data-category]/@data-category",
                    "selector_type": SelectorType.XPATH,
                    "multiple": True
                }
            }
            
            extractor = DataExtractor(extraction_config)
            result = extractor.extract(sample_html)
            
            assert result["title"] == "Sample Page Title"
            assert result["price_regex"] == ["19.99", "29.99"]
            assert result["categories"] == ["electronics", "home"]
        except ImportError:
            pytest.skip("lxml not installed, skipping combined selectors test")

    def test_transformations_with_extraction(self, sample_html: str) -> None:
        """Test applying transformations during extraction.
        
        Args:
            sample_html: Sample HTML string
        """
        extraction_config: Dict[str, ExtractorConfig] = {
            "title_upper": {
                "selector": "h1.main-title",
                "selector_type": SelectorType.CSS,
                "transform": "upper"
            },
            "price_numeric": {
                "selector": "p.price",
                "selector_type": SelectorType.CSS,
                "regex_pattern": r"\$([\d.]+)",
                "transform": "float"
            },
            "in_stock": {
                "selector": "p.stock",
                "selector_type": SelectorType.CSS,
                "attribute": "data-in-stock",
                "transform": "bool"
            }
        }
        
        extractor = DataExtractor(extraction_config)
        result = extractor.extract(sample_html)
        
        assert result["title_upper"] == "SAMPLE PAGE TITLE"
        assert result["price_numeric"] == 19.99
        assert result["in_stock"] is True  # Converted from "yes" 