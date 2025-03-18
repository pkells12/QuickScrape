"""
Version information for QuickScrape.
"""

from typing import Tuple


__version__ = "0.1.0"


def get_version() -> str:
    """
    Return the current version of QuickScrape.

    Returns:
        str: The version string in semver format (e.g., "0.1.0").
    """
    return __version__


def get_version_tuple() -> Tuple[int, int, int]:
    """
    Return the current version as a tuple of integers.

    Returns:
        Tuple[int, int, int]: The version as a tuple (major, minor, patch).
    """
    return tuple(map(int, __version__.split("."))) 