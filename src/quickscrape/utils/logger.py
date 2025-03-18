"""
Logging utilities for QuickScrape.

This module provides a consistent logging setup across the application.
"""

import logging
import os
import sys
from typing import Optional

from rich.logging import RichHandler


# Create a formatter for detailed logging
VERBOSE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(message)s"


def get_logger(
    name: str, 
    level: Optional[int] = None,
    rich_output: bool = True
) -> logging.Logger:
    """
    Get a logger configured with consistent formatting.

    Args:
        name: The name of the logger, typically __name__
        level: The logging level (defaults to INFO, or DEBUG if QUICKSCRAPE_DEBUG=1)
        rich_output: Whether to use Rich formatting for console output

    Returns:
        logging.Logger: Configured logger instance
    """
    # Determine the log level from environment variable or parameter
    if level is None:
        if os.environ.get("QUICKSCRAPE_DEBUG", "0") == "1":
            level = logging.DEBUG
        else:
            level = logging.INFO

    # Create or get the logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Only add handlers if they don't exist yet
    if not logger.handlers:
        if rich_output:
            # Use Rich for console output
            console_handler = RichHandler(rich_tracebacks=True)
            console_handler.setFormatter(logging.Formatter(SIMPLE_FORMAT))
        else:
            # Use standard console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(VERBOSE_FORMAT))
        
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    return logger


def configure_file_logging(log_dir: Optional[str] = None, level: int = logging.INFO) -> None:
    """
    Configure file-based logging for the application.

    Args:
        log_dir: Directory to store log files (defaults to ~/.quickscrape/logs)
        level: The logging level for the file handler
    """
    import datetime
    from pathlib import Path

    # Set up the log directory
    if log_dir is None:
        log_dir = os.environ.get("QUICKSCRAPE_LOG_DIR")
        if not log_dir:
            log_dir = str(Path.home() / ".quickscrape" / "logs")
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create a unique log filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"quickscrape_{timestamp}.log"

    # Create a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(VERBOSE_FORMAT))

    # Add the handler to the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Log the start of the session
    root_logger.info(f"Started logging to {log_file}")


def set_log_level(level: int) -> None:
    """
    Set the log level for all QuickScrape loggers.

    Args:
        level: The logging level to set
    """
    # Update the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Update all existing handlers
    for handler in root_logger.handlers:
        handler.setLevel(level)
    
    # Also update all existing QuickScrape loggers
    for name in logging.root.manager.loggerDict:
        if name.startswith("quickscrape"):
            logger = logging.getLogger(name)
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level) 