import logging
import sys

def setup_logger(name='smart_power_manager', level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():  
        logger.setLevel(logging.DEBUG)
        
        file_handler = logging.FileHandler('details_debug.txt', mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
    return logger