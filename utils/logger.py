import logging
import sys

def setup_logger(name='smart_power_manager', level=logging.INFO):
    """Set up logger with separate handlers for console and file output"""
    logger = logging.getLogger(name)
    if not logger.hasHandlers():  # Prevent adding multiple handlers
        logger.setLevel(logging.DEBUG)
        
        # File handler for important debug and info logs
        # File handler for all logs (debug, info, warning, error, critical)
        file_handler = logging.FileHandler('details_debug.txt', mode='a')
        file_handler.setLevel(logging.DEBUG) # Capture all levels to file
        file_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
    return logger