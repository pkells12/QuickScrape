"""Data extraction module for QuickScrape.

This module provides functionality for extracting structured data from web pages.
It includes selectors for various types of data extraction (CSS, XPath, regex).
"""

import re
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Pattern, Protocol, Union, TypedDict, cast

from bs4 import BeautifulSoup, Tag


class SelectorType(Enum):
    """Enum defining types of selectors available for data extraction."""
    CSS = auto()
    XPATH = auto()
    REGEX = auto()
    JSON_PATH = auto()


class ExtractorConfig(TypedDict, total=False):
    """Configuration options for data extractors."""
    selector: str
    selector_type: SelectorType
    multiple: bool
    attribute: Optional[str]
    default: Any
    transform: Optional[str]
    regex_pattern: Optional[str]
    regex_group: Optional[int]


class Extractor(Protocol):
    """Protocol defining the interface for data extractors."""
    
    def extract(self, source: Union[str, BeautifulSoup, Tag]) -> Any:
        """Extract data from the provided source.
        
        Args:
            source: The source to extract data from (HTML string, BeautifulSoup object, or Tag)
            
        Returns:
            The extracted data
        """
        ...


class BaseExtractor(ABC):
    """Base class for data extractors.
    
    Implements common functionality for all extractor types.
    """
    
    def __init__(self, config: ExtractorConfig) -> None:
        """Initialize the base extractor.
        
        Args:
            config: Configuration dictionary for the extractor
        """
        self.config = config
        self.multiple = config.get("multiple", False)
        self.attribute = config.get("attribute")
        self.default = config.get("default")
        
        # Compiled regex pattern if applicable
        self._regex_pattern: Optional[Pattern] = None
        if regex_pattern := config.get("regex_pattern"):
            self._regex_pattern = re.compile(regex_pattern)
        
        self._regex_group = config.get("regex_group", 0)
        
        # Transformation function name if applicable
        self._transform_name = config.get("transform")
    
    def _transform_value(self, value: Any) -> Any:
        """Apply transformation to the extracted value if specified.
        
        Args:
            value: The value to transform
            
        Returns:
            The transformed value
        """
        if value is None or not self._transform_name:
            return value
        
        transform_map = {
            "strip": lambda x: x.strip() if isinstance(x, str) else x,
            "lower": lambda x: x.lower() if isinstance(x, str) else x,
            "upper": lambda x: x.upper() if isinstance(x, str) else x,
            "int": lambda x: int(x) if x and isinstance(x, str) and x.strip().isdigit() else x,
            "float": lambda x: float(x) if x and isinstance(x, str) and re.match(r"^\s*\d+(\.\d+)?\s*$", x) else x,
            "bool": lambda x: bool(x),
        }
        
        transform_func = transform_map.get(self._transform_name)
        if not transform_func:
            return value
        
        try:
            if isinstance(value, list):
                return [transform_func(item) for item in value]
            return transform_func(value)
        except (ValueError, TypeError):
            return value
    
    def _apply_regex(self, value: str) -> Union[str, None]:
        """Apply regex pattern to the extracted string value if specified.
        
        Args:
            value: The string value to apply regex to
            
        Returns:
            The extracted regex group or None if no match
        """
        if not self._regex_pattern or not isinstance(value, str):
            return value
        
        match = self._regex_pattern.search(value)
        if not match:
            return None
        
        return match.group(self._regex_group)
    
    def _process_element(self, element: Tag) -> Any:
        """Process a single BeautifulSoup element based on configuration.
        
        Args:
            element: The BeautifulSoup Tag to process
            
        Returns:
            The extracted data according to configuration
        """
        value: Any = None
        
        # Extract attribute or text
        if self.attribute:
            if self.attribute == "html":
                value = str(element)
            else:
                value = element.get(self.attribute)
        else:
            value = element.get_text()
        
        # Apply regex if applicable
        if isinstance(value, str) and self._regex_pattern:
            value = self._apply_regex(value)
        
        # Apply transformation
        return self._transform_value(value)
    
    @abstractmethod
    def extract(self, source: Union[str, BeautifulSoup, Tag]) -> Any:
        """Extract data from the source.
        
        Args:
            source: The source to extract data from
            
        Returns:
            The extracted data
        """
        pass


class CssExtractor(BaseExtractor):
    """Extractor that uses CSS selectors."""
    
    def __init__(self, config: ExtractorConfig) -> None:
        """Initialize the CSS extractor.
        
        Args:
            config: Configuration dictionary for the extractor
        """
        super().__init__(config)
        self.selector = config["selector"]
    
    def extract(self, source: Union[str, BeautifulSoup, Tag]) -> Any:
        """Extract data using CSS selectors.
        
        Args:
            source: HTML source as string, BeautifulSoup object, or Tag
            
        Returns:
            The extracted data
        """
        # Convert string to BeautifulSoup if needed
        if isinstance(source, str):
            soup = BeautifulSoup(source, "html.parser")
        else:
            soup = source if isinstance(source, BeautifulSoup) else BeautifulSoup(str(source), "html.parser")
        
        # Select elements
        elements = soup.select(self.selector)
        
        if not elements:
            return self.default
        
        if self.multiple:
            return [self._process_element(el) for el in elements]
        
        return self._process_element(elements[0])


class XPathExtractor(BaseExtractor):
    """Extractor that uses XPath selectors."""
    
    def __init__(self, config: ExtractorConfig) -> None:
        """Initialize the XPath extractor.
        
        Args:
            config: Configuration dictionary for the extractor
        """
        super().__init__(config)
        self.selector = config["selector"]
        
        # Import lxml only when needed
        try:
            from lxml import etree
            self._etree = etree
        except ImportError:
            raise ImportError("lxml is required for XPath extraction. Install it with 'pip install lxml'.")
    
    def extract(self, source: Union[str, BeautifulSoup, Tag]) -> Any:
        """Extract data using XPath selectors.
        
        Args:
            source: HTML source as string, BeautifulSoup object, or Tag
            
        Returns:
            The extracted data
        """
        # Convert to string if BeautifulSoup
        if isinstance(source, (BeautifulSoup, Tag)):
            html_string = str(source)
        else:
            html_string = source
        
        # Parse with lxml
        html_doc = self._etree.HTML(html_string)
        elements = html_doc.xpath(self.selector)
        
        if not elements:
            return self.default
        
        # Process the result
        if self.multiple:
            result = []
            for el in elements:
                if isinstance(el, self._etree._Element):
                    # Convert lxml element to string and then to BeautifulSoup
                    el_html = self._etree.tostring(el, encoding="unicode")
                    soup_el = BeautifulSoup(el_html, "html.parser")
                    result.append(self._process_element(soup_el))
                else:
                    # For text nodes or attributes
                    value = str(el)
                    if self._regex_pattern:
                        value = self._apply_regex(value) or value
                    result.append(self._transform_value(value))
            return result
        
        # Single element
        if isinstance(elements[0], self._etree._Element):
            el_html = self._etree.tostring(elements[0], encoding="unicode")
            soup_el = BeautifulSoup(el_html, "html.parser")
            return self._process_element(soup_el)
        
        # Text or attribute
        value = str(elements[0])
        if self._regex_pattern:
            value = self._apply_regex(value) or value
        return self._transform_value(value)


class RegexExtractor(BaseExtractor):
    """Extractor that uses regular expressions."""
    
    def __init__(self, config: ExtractorConfig) -> None:
        """Initialize the regex extractor.
        
        Args:
            config: Configuration dictionary for the extractor
        """
        super().__init__(config)
        
        # Use the main regex pattern from config or from regex_pattern
        pattern = config["selector"]
        self._pattern = re.compile(pattern, re.DOTALL)
        self._group = config.get("regex_group", 1)  # Default to group 1 for main pattern
    
    def extract(self, source: Union[str, BeautifulSoup, Tag]) -> Any:
        """Extract data using regular expressions.
        
        Args:
            source: HTML source as string, BeautifulSoup object, or Tag
            
        Returns:
            The extracted data
        """
        # Convert to string if BeautifulSoup
        if isinstance(source, (BeautifulSoup, Tag)):
            text = source.get_text() if not self.attribute else source.get(self.attribute, "")
            if self.attribute == "html":
                text = str(source)
        else:
            text = source
        
        # Find all matches if multiple
        if self.multiple:
            matches = self._pattern.finditer(text)
            result = [match.group(self._group) for match in matches]
            
            # Apply secondary regex if needed
            if self._regex_pattern:
                result = [self._apply_regex(item) or item for item in result]
            
            return self._transform_value(result) if result else self.default
        
        # Find single match
        match = self._pattern.search(text)
        if not match:
            return self.default
        
        value = match.group(self._group)
        
        # Apply secondary regex if needed
        if self._regex_pattern:
            value = self._apply_regex(value) or value
        
        return self._transform_value(value)


class DataExtractor:
    """Main data extraction class for processing HTML with multiple extractors."""
    
    def __init__(self, extraction_config: Dict[str, ExtractorConfig]) -> None:
        """Initialize the data extractor with a configuration map.
        
        Args:
            extraction_config: A dictionary mapping field names to extractor configurations
        """
        self.extractors: Dict[str, Extractor] = {}
        
        # Create extractors based on config
        for field_name, config in extraction_config.items():
            selector_type = config.get("selector_type", SelectorType.CSS)
            
            if selector_type == SelectorType.CSS:
                self.extractors[field_name] = CssExtractor(config)
            elif selector_type == SelectorType.XPATH:
                self.extractors[field_name] = XPathExtractor(config)
            elif selector_type == SelectorType.REGEX:
                self.extractors[field_name] = RegexExtractor(config)
            # JSON_PATH would be implemented here
    
    def extract(self, html: str) -> Dict[str, Any]:
        """Extract all configured data from the HTML.
        
        Args:
            html: HTML string to extract data from
            
        Returns:
            A dictionary with field names and their extracted values
        """
        soup = BeautifulSoup(html, "html.parser")
        result: Dict[str, Any] = {}
        
        for field_name, extractor in self.extractors.items():
            result[field_name] = extractor.extract(soup)
        
        return result 