"""
Pytest configuration for QuickScrape tests.
"""

import os
import sys
from typing import List

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def pytest_collection_modifyitems(items: List) -> None:
    """
    Add markers to tests based on their path.

    Args:
        items: List of collected test items
    """
    for item in items:
        if "unit" in item.nodeid:
            item.add_marker("unit")
        elif "integration" in item.nodeid:
            item.add_marker("integration")
        elif "e2e" in item.nodeid:
            item.add_marker("e2e") 