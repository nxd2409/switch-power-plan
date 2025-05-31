import time
import logging
import threading
import signal
import datetime
import os
from .activity_monitor import ActivityMonitor
from .process_monitor import ProcessMonitor
from .power_manager_windows import PowerManagerWindows

logger = logging.getLogger(__name__)

class PowerController:
    def __init__(self, settings):
        # Đọc các cấu hình cơ bản
        self.idle_threshold = settings.getint('General', 'idle_threshold_seconds', fallback=300)
        self.check_interval = settings.getint('General', 'check_interval_seconds', fallback=10)
        
        # Initialize components
        heavy_processes = settings.get('Processes', 'heavy_processes', fallback='').split(',')
        heavy_processes = [p.strip() for p in heavy_processes if p.strip()]
        
        self.process_monitor = ProcessMonitor(heavy_processes, turbo_config=settings)
        self.activity_monitor = ActivityMonitor(self.idle_threshold)
        
        # Initialize power manager with GUIDs from settings
        try:
            high_perf_guid = settings.get('PowerPlans', 'high_performance_guid')
            balanced_guid = settings.get('PowerPlans', 'balanced_guid')
            power_saver_guid = settings.get('PowerPlans', 'power_saver_guid')
            turbo_guid = settings.get('PowerPlans', 'turbo_guid', fallback=None)
            
            self.power_manager = PowerManagerWindows(high_perf_guid, balanced_guid, power_saver_guid, turbo_guid)
            self.power_manager_error = None
            logger.info("PowerManager initialized successfully")
            
        except PermissionError as e:
            self.power_manager = None
            self.power_manager_error = str(e)
            logger.error(f"Failed to initialize PowerManager: {e}")
            
        except Exception as e:
            self.power_manager = None
            self.power_manager_error = str(e)
            logger.error(f"Unexpected error initializing PowerManager: {e}")
        
        self.running = False
        self.last_status = None
        self.last_power_plan = None
        self._previous_manual_power_plan = None
        logger.debug(f"[DEBUG] Initial _previous_manual_power_plan: {self._previous_manual_power_plan}")
        
        # Activity log file
        self.activity_log_file = os.path.join("logs", "activity_debug.txt")
        
        logger.info(f"PowerController initialized with idle threshold: {self.idle_threshold}s")
        
    def write_to_activity_log(self, message):
        """Write a message to the activity log file"""
        try:
            with open(self.activity_log_file, 'a', encoding='utf-8') as f:
                f.write(message + "\n")
        except Exception as e:
            logger.error(f"Error writing to activity log: {e}")
            
    def handle_signal(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        logger.info("Received signal to stop. Cleaning up...")
        self.write_to_activity_log(f"\n--- Smart Power Manager stopped at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        self.running = False

    def run(self):
        """Main control loop"""
        self.running = True
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        # Check if PowerManager initialized successfully
        if not self.power_manager:
            logger.error(f"Cannot run without PowerManager: {self.power_manager_error}")
            return False

        # Capture the initial power plan when the application starts
        if self._previous_manual_power_plan is None:
            initial_plan = self.power_manager.get_current_plan_name()
            if initial_plan:
                self._previous_manual_power_plan = initial_plan
                logger.info(f"Initial power plan detected: {self._previous_manual_power_plan}")
            else:
                logger.warning("Could not detect initial power plan.")
            logger.debug(f"[DEBUG] _previous_manual_power_plan after initial capture: {self._previous_manual_power_plan}")

        # Start monitoring for activity
        if not self.activity_monitor.start_monitoring():
            logger.error("Failed to start activity monitoring")
            return False
        
        # Write startup information to log
        start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.write_to_activity_log(f"\n\n--- Starting Smart Power Manager ---\n")
        self.write_to_activity_log(f"Time: {start_time}")
        self.write_to_activity_log(f"Check interval: {self.check_interval}s")
        self.write_to_activity_log(f"Idle threshold: {self.idle_threshold}s\n")
        
        logger.info("Smart Power Manager is running. Press Ctrl+C to stop.")
        
        start_time = time.time()
        
        try:
            while self.running:
                try:
                    # Get current states
                    is_idle = self.activity_monitor.is_user_idle()
                    elapsed_time = int(time.time() - start_time)
                    
                    # Check conditions in order of priority
                    # 1. First check Turbo condition (highest priority)
                    turbo_result = self.process_monitor.check_turbo_condition()
                    is_turbo, running_apps = turbo_result
                    
                    # 2. Then check for heavy processes if not in turbo mode
                    is_heavy_running = False if is_turbo else self.process_monitor.is_heavy_process_running()
                    
                    # Determine power plan based on conditions with priority
                    if is_turbo:
                        desired_plan = 'turbo'
                        status_msg = f"Turbo Mode → {', '.join(running_apps)}"
                    elif is_heavy_running and not is_idle:
                        # Only go to high performance if not idle
                        desired_plan = 'high_performance'
                        status_msg = "Heavy process active → Performance Mode"
                    elif is_idle:
                        # If system is idle, go to power saver regardless of running apps
                        desired_plan = 'power_saver'
                        status_msg = "System idle → Power Saver Mode"
                    else:
                        # Default to balanced mode
                        desired_plan = 'balanced'
                        status_msg = "Normal usage → Balanced Mode"
                    
                    # Only log and apply changes when the power plan changes
                    if desired_plan != self.last_power_plan:
                        logger.info(status_msg)
                        self.last_status = status_msg
                        self.last_power_plan = desired_plan
                        
                        # Apply the new power plan
                        if not self.power_manager.set_power_plan(desired_plan):
                            logger.error(f"Failed to set power plan to {desired_plan}")
                            # Check if we lost admin rights
                            if not self.power_manager._is_admin():
                                logger.error("Lost administrator privileges! Please run the application as administrator.")
                                self.running = False
                                break
                    
                    # Write status to activity log regardless of changes
                    current_time = datetime.datetime.now().strftime('%H:%M:%S')
                    # Prepare running apps info for logging
                    log_msg = f"{current_time} - Turbo: {is_turbo}, Heavy: {is_heavy_running}, Idle: {is_idle} ({elapsed_time}s), Action: {desired_plan}"
                    self.write_to_activity_log(log_msg)
                    
                    # Sleep until next check
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"Error during check cycle: {e}", exc_info=True)
                    if "access denied" in str(e).lower() or "permission" in str(e).lower():
                        logger.error("Lost administrator privileges! Please run the application as administrator.")
                        self.running = False
                        break
                    time.sleep(self.check_interval)

        finally:
            # Cleanup when stopping
            logger.info("Stopping Smart Power Manager...")
            self.activity_monitor.stop_monitoring()
            # Restore previous manual power plan if it was set, otherwise set to balanced
            if self.power_manager and self.power_manager._is_admin():
                logger.debug(f"[DEBUG] Attempting to restore power plan. _previous_manual_power_plan: {self._previous_manual_power_plan}")
                if self._previous_manual_power_plan:
                    logger.info(f"Restoring previous power plan: {self._previous_manual_power_plan}")
                    self.power_manager.set_power_plan(self._previous_manual_power_plan)
                else:
                    logger.info("No previous manual power plan to restore, setting to balanced.")
                    self.power_manager.set_power_plan('balanced')
            # Write stop message to log if not already written by signal handler
            if self.running:
                self.write_to_activity_log(f"\n--- Smart Power Manager stopped at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            logger.info("Smart Power Manager stopped.")
            return True