"""
Professional logging system for CG Spins Bot
Provides structured logging with different levels and proper formatting
"""

import logging
import sys
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # Add timestamp
        record.timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format the message
        return super().format(record)

def setup_logger(name: str = "CGSpinsBot", level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a professional logger with console and optional file output
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
    
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    console_formatter = ColoredFormatter(
        '%(timestamp)s | %(levelname)s | %(name)s | %(message)s'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler for {log_file}: {e}")
    
    return logger

def get_logger(name: str = "CGSpinsBot") -> logging.Logger:
    """
    Get a logger instance, creating it if it doesn't exist
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

# Create default logger
default_logger = setup_logger() 