import os
import sys
import subprocess
import configparser
import ctypes
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('service_installer')

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_service():
    """Install and configure the Smart Power Manager Windows service."""
    logger.info("Starting Smart Power Manager service installation...")
    
    # Check if running as admin
    if not is_admin():
        logger.error("This script must be run as Administrator.")
        print("This script must be run as Administrator. Please restart with admin privileges.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Ensure the required packages are installed
    try:
        logger.info("Ensuring required packages are installed...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        logger.info("Required packages installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install required packages: {e}")
        print(f"Failed to install required packages. Please check {e.stderr.decode()}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Check if the service is already installed
    try:
        service_status = subprocess.run(["sc", "query", "SmartPowerManager"], 
                                      capture_output=True, text=True)
        if service_status.returncode == 0:
            logger.info("Service is already installed. Uninstalling first...")
            try:
                subprocess.run([sys.executable, "windows_service.py", "remove"], 
                              check=True, capture_output=True)
                logger.info("Previous service installation removed.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to remove existing service: {e}")
                print(f"Failed to remove existing service. You may need to manually remove it.")
                input("Press Enter to continue anyway...")
    except subprocess.CalledProcessError:
        # Service does not exist, which is fine
        logger.info("Service not currently installed.")
    
    # Install the service
    try:
        logger.info("Installing service...")
        subprocess.run([sys.executable, "windows_service.py", "install"], 
                      check=True, capture_output=True)
        logger.info("Service installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install service: {e}")
        print(f"Failed to install service: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Check if autostart is enabled in config
    try:
        logger.info("Reading configuration...")
        config = configparser.ConfigParser()
        config.read(os.path.join('config', 'settings.ini'))
        
        autostart = config.getint('General', 'enable_autostart', fallback=0)
        if autostart:
            logger.info("Autostart is enabled. Configuring service to start automatically...")
            subprocess.run(["sc", "config", "SmartPowerManager", "start=", "auto"], 
                          check=True, capture_output=True)
            logger.info("Service configured for automatic start.")
        else:
            logger.info("Autostart is disabled. Configuring service for manual start...")
            subprocess.run(["sc", "config", "SmartPowerManager", "start=", "demand"], 
                          check=True, capture_output=True)
            logger.info("Service configured for manual start.")
    except Exception as e:
        logger.error(f"Failed to configure service startup: {e}")
        print(f"Warning: Service installed but startup configuration failed: {e}")
    
    # Start the service if autostart is enabled
    if autostart:
        try:
            logger.info("Starting service...")
            subprocess.run(["sc", "start", "SmartPowerManager"], check=True, capture_output=True)
            logger.info("Service started successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start service: {e}")
            print(f"Warning: Service installed but failed to start: {e.stderr.decode() if e.stderr else 'Unknown error'}")
    
    logger.info("Installation completed!")
    print("\nSmart Power Manager service has been successfully installed!")
    if autostart:
        print("The service is configured to start automatically with Windows and has been started.")
    else:
        print("The service is configured for manual start. To start it, use: sc start SmartPowerManager")
    print("\nTo uninstall, run: python windows_service.py remove")
    print("To check service status: sc query SmartPowerManager")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    install_service() 