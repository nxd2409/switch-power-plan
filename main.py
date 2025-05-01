import configparser
import logging
import os
import sys
import time
import datetime

from core.controller import PowerController
from utils.logger import setup_logger

CONFIG_FILE = os.path.join('config', 'settings.ini')

def load_config(config_path):
    # Clear old log file
    try:
        if os.path.exists('activity_debug.txt'):
            os.remove('activity_debug.txt')
    except:
        pass
        
    if not os.path.exists(config_path):
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(f"Error: Configuration file not found at {config_path}")

    config = configparser.ConfigParser()
    try:
        # Đọc file với encoding UTF-8
        with open(config_path, 'r', encoding='utf-8') as f:
            config.read_file(f)
            
        # Basic validation
        if not config.has_section('General') or \
           not config.has_section('PowerPlans') or \
           not config.has_section('Processes'):
            raise configparser.Error("Missing required sections in config file.")
            
        # Kiểm tra enable_debug_logging
        debug_enabled = config.getboolean('General', 'enable_debug_logging', fallback=False)
        logger = setup_logger(level=logging.DEBUG if debug_enabled else logging.INFO)
        logger.info(f"Debug logging is {'enabled' if debug_enabled else 'disabled'}")
        
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
    except configparser.Error as e:
        logging.error(f"Error parsing configuration file {config_path}: {e}")
        sys.exit(f"Error: Could not parse configuration file: {e}")
    except UnicodeDecodeError as e:
        logging.error(f"Encoding error reading {config_path}: {e}")
        sys.exit(f"Error: File encoding issue. Please ensure the file is saved in UTF-8 format.")
    except Exception as e:
        logging.error(f"Unexpected error reading {config_path}: {e}")
        sys.exit(f"Error: Could not read configuration file: {e}")

def main():
    # Write startup banner
    with open('activity_debug.txt', 'a', encoding='utf-8') as f:
        f.write(f"\n\n--- Starting Smart Power Manager ---\n")
        f.write(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load configuration
    logger = logging.getLogger('smart_power_manager')
    logger.debug("Loading configuration...")
    config = load_config(CONFIG_FILE)
    logger.debug("Configuration loaded.")

    # Check for placeholder GUIDs and warn user
    power_settings = config['PowerPlans']
    if "placeholder" in power_settings.get('high_performance_guid', '') or \
       "placeholder" in power_settings.get('balanced_guid', '') or \
       "placeholder" in power_settings.get('power_saver_guid', ''):
        logger.warning("!!! Placeholder Power Plan GUIDs detected in config/settings.ini !!!")
        logger.warning("Please run 'powercfg /list' in your command prompt and update the GUIDs.")
        logger.warning("The application might not function correctly until the GUIDs are set.")

    # Initialize and run the controller
    logger.debug("Initializing PowerController...")
    try:
        controller = PowerController(config)
        logger.debug("PowerController initialized successfully.")
        logger.info("Starting Smart Power Manager...")
        
        # Run the controller in the main thread
        controller.run()
            
    except Exception as e:
        logger.critical(f"An unexpected error occurred during controller initialization or run: {e}", exc_info=True)
        sys.exit(f"An critical error occurred: {e}")

    logger.info("Smart Power Manager finished.")

if __name__ == "__main__":
    main()