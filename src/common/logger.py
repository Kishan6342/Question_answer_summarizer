import logging
import sys
from typing import Optional

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger instance"""
    
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger
