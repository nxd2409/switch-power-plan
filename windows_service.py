import os
import sys
import time
import logging
import configparser
import win32serviceutil
import win32service
import win32event
import servicemanager

# Add the parent directory to the path so we can import our own modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.controller import PowerController
from utils.logger import setup_logger

class SmartPowerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SmartPowerManager"
    _svc_display_name_ = "Smart Power Manager"
    _svc_description_ = "Automatically manages power plans based on system usage and user activity."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.controller = None
        
        # Set up logging to a file in the service context
        # Use a directory that the service can write to
        log_dir = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'SmartPowerManager', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'smart_power_service.log')
        
        # Setup file logging - service can't log to console
        self.logger = logging.getLogger('smart_power_manager')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        
        # Stop the controller
        if self.controller and self.controller.running:
            self.logger.info("Service stopping - shutting down controller...")
            self.controller.stop()
        
        self.logger.info("Service stop initiated.")

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        self.logger.info("Smart Power Manager service starting...")
        
        try:
            # Load configuration
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'settings.ini')
            if not os.path.exists(config_path):
                self.logger.error(f"Configuration file not found: {config_path}")
                return
                
            config = configparser.ConfigParser()
            config.read(config_path)
            self.logger.info("Configuration loaded successfully.")
            
            # Create and start the controller
            self.controller = PowerController(config)
            if not self.controller.run():
                self.logger.error("Failed to start the power controller.")
                return
                
            self.logger.info("Smart Power Manager service started and running.")
            
            # Main service loop - just wait for stop event
            while True:
                # Check if service is being stopped
                if win32event.WaitForSingleObject(self.stop_event, 1000) != win32event.WAIT_TIMEOUT:
                    break
                    
                # Nothing to do here as controller runs in its own thread
                time.sleep(1)
        
        except Exception as e:
            self.logger.error(f"Service encountered an error: {e}", exc_info=True)
        
        finally:
            if self.controller and self.controller.running:
                self.controller.stop()
            self.logger.info("Smart Power Manager service stopped.")

# This allows the service to be run from the command line for testing
if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SmartPowerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SmartPowerService) 