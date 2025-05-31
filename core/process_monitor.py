import psutil
import logging
import win32gui
import win32process
import win32con
import time
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger('process_monitor', logging.DEBUG)

class ProcessMonitor:
    def __init__(self, heavy_process_names, turbo_config=None):
        # Store names in lowercase for case-insensitive comparison
        self.heavy_process_names = {name.lower() for name in heavy_process_names}
        
        # Turbo mode configuration
        self.min_apps_threshold = turbo_config.getint('TurboMode', 'min_apps_threshold', fallback=2) if turbo_config else 2
        self.turbo_apps = {name.strip().lower() for name in turbo_config.get('TurboMode', 'turbo_apps', fallback='').split(',') if name.strip()} if turbo_config else set()
        
        logger.info("=== ProcessMonitor Initialization ===")
        logger.info(f"Heavy processes configured: {self.heavy_process_names}")
        logger.info(f"Turbo mode threshold: {self.min_apps_threshold} apps")
        logger.info(f"Turbo apps configured: {self.turbo_apps}")

        
        # Cache state
        self._cache_lifetime = 2.0  # seconds
        self._window_cache = {}  # (proc_name, pid) -> (timestamp, has_window)
        self._last_active_processes = set()
        self._last_turbo_state = (False, set())
        self._last_heavy_state = False
        self._last_check_time = 0
        self._skipped_processes_count = 0

    def _get_cached_window_state(self, proc_name, pid):
        """Get cached window state if still valid"""
        cache_key = (proc_name, pid)
        if cache_key in self._window_cache:
            timestamp, has_window = self._window_cache[cache_key]
            if time.time() - timestamp < self._cache_lifetime:
                return has_window
        return None

    def _update_window_cache(self, proc_name, pid, has_window):
        """Update the window state cache"""
        self._window_cache[(proc_name, pid)] = (time.time(), has_window)

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        now = time.time()
        expired = []
        for key, (timestamp, _) in self._window_cache.items():
            if now - timestamp >= self._cache_lifetime:
                expired.append(key)
        for key in expired:
            del self._window_cache[key]

    def has_visible_window(self, proc_name, pid):
        """Check if process has visible and active windows"""
        def callback(hwnd, hwnds):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if found_pid == pid:
                        title = win32gui.GetWindowText(hwnd)
                        
                        # Skip empty or hidden windows, but allow Program Manager
                        if not title and title != "Program Manager":
                            return True

                        # Check window style and size
                        try:
                            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                            if not (style & win32con.WS_VISIBLE):
                                return True

                            rect = win32gui.GetWindowRect(hwnd)
                            width = rect[2] - rect[0]
                            height = rect[3] - rect[1]
                            if width <= 50 or height <= 50:
                                return True
                            
                            # Valid window found
                            hwnds.append((hwnd, title, width, height))
                            
                        except Exception as e:
                            logger.debug(f"Error checking window style - Process: {proc_name}, Error: {e}")
                            if title == "Program Manager" or (width > 50 and height > 50):
                                hwnds.append((hwnd, title, width, height))
                                
            except Exception as e:
                logger.debug(f"Error checking window - HWND: {hwnd}, Error: {e}")
            return True

        hwnds = []
        try:
            win32gui.EnumWindows(callback, hwnds)
            if hwnds:
                logger.debug(f"Found {len(hwnds)} valid windows for {proc_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error enumerating windows for {proc_name}: {e}")
            return False

    def get_active_processes_with_windows(self):
        """Get list of running processes with visible windows"""
        current_time = time.time()
        if current_time - self._last_check_time < self._cache_lifetime:
            return self._last_active_processes

        self._last_check_time = current_time
        self._cleanup_cache()
        
        active_processes = set()
        self._skipped_processes_count = 0
        
        for process in psutil.process_iter(['name', 'pid']):
            try:
                proc_name = process.info.get('name', '').lower()
                proc_pid = process.info.get('pid', 0)
                
                # Skip known background processes
                if any(x in proc_name for x in ["svchost", "runtime", "broker", "service", "helper", "system"]):
                    self._skipped_processes_count += 1
                    continue
                
                # Check cache
                cached_state = self._get_cached_window_state(proc_name, proc_pid)
                if cached_state is not None:
                    if cached_state:
                        active_processes.add(proc_name)
                    continue
                
                # Check for visible windows
                if self.has_visible_window(proc_name, proc_pid):
                    active_processes.add(proc_name)
                    self._update_window_cache(proc_name, proc_pid, True)
                else:
                    self._update_window_cache(proc_name, proc_pid, False)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        logger.debug(f"Process scan complete: {len(active_processes)} active, {self._skipped_processes_count} background skipped")
        
        # Update cache
        self._last_active_processes = active_processes
        return active_processes

    def check_turbo_condition(self):
        """Check conditions for activating Turbo Mode"""
        try:
            active_processes = self.get_active_processes_with_windows()
            heavy_running_apps = self.heavy_process_names.intersection(active_processes)
            
            turbo_running_apps = {app for app in active_processes if app in self.turbo_apps}

            # Condition 1: At least one app from turbo_apps is running
            condition_turbo_apps = bool(turbo_running_apps)

            # Condition 2: At least min_apps_threshold (default 2) from heavy_process_names are running
            condition_heavy_apps = len(heavy_running_apps) >= self.min_apps_threshold

            if condition_turbo_apps or condition_heavy_apps:
                current_state = (True, turbo_running_apps.union(heavy_running_apps))
                if current_state != self._last_turbo_state:
                    if condition_turbo_apps and not condition_heavy_apps:
                        logger.info(f"Turbo mode activated by turbo_apps: {turbo_running_apps}")
                    elif condition_heavy_apps and not condition_turbo_apps:
                        logger.info(f"Turbo mode activated by heavy_apps: {heavy_running_apps} (>= {self.min_apps_threshold} apps)")
                    else:
                        logger.info(f"Turbo mode activated by both turbo_apps ({turbo_running_apps}) and heavy_apps ({heavy_running_apps})")
                    self._last_turbo_state = current_state
                return current_state
            
            if self._last_turbo_state[0]:
                logger.info("Turbo mode deactivated")
                self._last_turbo_state = (False, set())
                
            return (False, set())

        except Exception as e:
            logger.error(f"Error checking turbo condition: {e}")
            return (False, set())

    def is_heavy_process_running(self):
        """Check if any heavy process is running with visible windows"""
        try:
            active_processes = self.get_active_processes_with_windows()
            heavy_running = self.heavy_process_names.intersection(active_processes)
            
            is_heavy = bool(heavy_running)
            if is_heavy != self._last_heavy_state:
                if is_heavy:
                    logger.info(f"Heavy processes detected: {', '.join(heavy_running)}")
                else:
                    logger.debug("No heavy processes active")
                self._last_heavy_state = is_heavy
            return is_heavy
        except Exception as e:
            logger.error(f"Error checking heavy process: {e}")
            return False

    def get_heavy_running_apps(self):
        """Return a list of currently running heavy processes with visible windows"""
        try:
            active_processes = self.get_active_processes_with_windows()
            heavy_running = self.heavy_process_names.intersection(active_processes)
            return list(heavy_running)
        except Exception as e:
            logger.error(f"Error getting heavy running apps: {e}")
            return []
            
            return is_heavy

        except Exception as e:
            logger.error(f"Error checking heavy processes: {e}")
            return False