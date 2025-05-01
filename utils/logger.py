import logging
import sys

def setup_logger(name='smart_power_manager', level=logging.INFO):
    """Set up logger with separate handlers for console and file output"""
    logger = logging.getLogger(name)
    if not logger.hasHandlers():  # Prevent adding multiple handlers
        logger.setLevel(logging.DEBUG)
        
        # File handler for important debug and info logs
        debug_handler = logging.FileHandler('activity_debug.txt', mode='a')
        debug_handler.setLevel(logging.INFO)  # Changed from DEBUG to INFO
        debug_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        debug_handler.setFormatter(debug_formatter)
        logger.addHandler(debug_handler)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
    return logger