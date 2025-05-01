import subprocess
import logging
import ctypes
import os
import winreg

logger = logging.getLogger(__name__)

class PowerManagerAsus:
    """Power manager specialized for ASUS laptops, using standard Windows powercfg and ASUS-specific operation modes."""
    
    # ASUS operation modes
    ASUS_MODE_SILENT = 0
    ASUS_MODE_PERFORMANCE = 1
    ASUS_MODE_TURBO = 2
    
    # Registry paths for ASUS operation mode
    ASUS_REGISTRY_PATHS = [
        r"SOFTWARE\ASUS\ARMOURY CRATE Service",
    ]
    
    def __init__(self, high_perf_guid, balanced_guid, power_saver_guid):
        """Initialize with standard Windows power plan GUIDs."""
        self.high_perf_guid = high_perf_guid
        self.balanced_guid = balanced_guid
        self.power_saver_guid = power_saver_guid
        self.current_plan = self._get_current_power_plan()
        self.current_asus_mode = self._get_current_asus_mode()
        
        logger.info(f"PowerManagerAsus initialized. Current plan: {self.current_plan}, ASUS mode: {self.current_asus_mode}")
    
    def _is_admin(self):
        """Check if the script is running with administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            logger.warning("Could not check admin status.")
            return False

    def _run_powercfg(self, args):
        """Run powercfg command with the given arguments."""
        if not self._is_admin():
            logger.error("Administrator privileges required to run powercfg.")
            return None
            
        try:
            cmd = ["powercfg"] + args
            logger.debug(f"Running powercfg command: {' '.join(cmd)}")
            
            # Use shell=True for better compatibility on Windows
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            logger.debug(f"powercfg output: {result.stdout.strip()}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running powercfg {args}: {e}")
            logger.error(f"Stderr: {e.stderr}")
            return None
        except FileNotFoundError:
             logger.error(f"'powercfg' command not found. Ensure it's in the system PATH.")
             return None
        except Exception as e:
            logger.error(f"Unexpected error running powercfg: {e}")
            return None
    
    def _get_current_power_plan(self):
        """Get the current active power plan using Windows powercfg."""
        output = self._run_powercfg(["/getactivescheme"])
        windows_plan = "unknown"
        
        if output and "GUID:" in output:
            try:
                guid = output.split("GUID:")[1].split("(")[0].strip()
                logger.info(f"Current active power plan GUID: {guid}")
                
                # Determine plan name from Windows perspective
                if guid.lower() == self.high_perf_guid.lower():
                    windows_plan = "high_performance"
                elif guid.lower() == self.balanced_guid.lower():
                    windows_plan = "balanced"
                elif guid.lower() == self.power_saver_guid.lower():
                    windows_plan = "power_saver"
                else:
                    # Attempt to get the name for custom plans
                    plan_name_raw = output.split("(")[-1].split(")")[0].strip()
                    logger.info(f"Custom power plan detected: {plan_name_raw} ({guid})")
                    # We can't reliably map custom plans, return 'custom' or the name if needed
                    windows_plan = "custom" # or plan_name_raw if you want the name
            except Exception as e:
                logger.warning(f"Could not parse power scheme GUID from powercfg output: {e}")
        else:
             logger.warning("Could not get active scheme via powercfg.")

        if windows_plan == "unknown":
            logger.warning("Could not determine the current power plan.")
            
        return windows_plan
    
    def _get_current_asus_mode(self):
        """Get the current ASUS operation mode from registry."""
        # Try different registry keys and value names
        registry_values = ["PerformanceMode", "Profile", "GameProfile"]
        
        for registry_path in self.ASUS_REGISTRY_PATHS:
            for value_name in registry_values:
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
                    value, _ = winreg.QueryValueEx(key, value_name)
                    winreg.CloseKey(key)
                    
                    logger.debug(f"Found ASUS mode value {value} in {registry_path} with key {value_name}")
                    
                    # Map numeric value to mode name
                    if value == self.ASUS_MODE_SILENT:
                        return "silent"
                    elif value == self.ASUS_MODE_PERFORMANCE:
                        return "performance"
                    elif value == self.ASUS_MODE_TURBO:
                        return "turbo"
                    else:
                        logger.debug(f"Unknown ASUS mode value: {value}")
                except Exception as e:
                    logger.debug(f"Could not read ASUS mode from {registry_path}/{value_name}: {e}")
        
        # Try HKEY_LOCAL_MACHINE as fallback
        for registry_path in self.ASUS_REGISTRY_PATHS:
            for value_name in registry_values:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path)
                    value, _ = winreg.QueryValueEx(key, value_name)
                    winreg.CloseKey(key)
                    
                    logger.debug(f"Found ASUS mode value {value} in HKLM\\{registry_path} with key {value_name}")
                    
                    # Map numeric value to mode name
                    if value == self.ASUS_MODE_SILENT:
                        return "silent"
                    elif value == self.ASUS_MODE_PERFORMANCE:
                        return "performance"
                    elif value == self.ASUS_MODE_TURBO:
                        return "turbo"
                    else:
                        logger.debug(f"Unknown ASUS mode value: {value}")
                except Exception as e:
                    logger.debug(f"Could not read ASUS mode from HKLM\\{registry_path}/{value_name}: {e}")
        
        logger.warning("Could not determine current ASUS operation mode")
        return "unknown"
    
    def set_asus_operation_mode(self, mode_name):
        """Set the ASUS-specific operation mode (Silent, Performance, Turbo)."""
        # Map mode name to numeric value
        mode_value = None
        if mode_name.lower() == "silent":
            mode_value = self.ASUS_MODE_SILENT
        elif mode_name.lower() == "performance":
            mode_value = self.ASUS_MODE_PERFORMANCE
        elif mode_name.lower() == "turbo":
            mode_value = self.ASUS_MODE_TURBO
        else:
            logger.warning(f"Unknown ASUS operation mode: {mode_name}")
            return False
        
        # Check current mode before changing
        current_mode = self._get_current_asus_mode()
        if current_mode == mode_name.lower():
            logger.debug(f"ASUS operation mode already set to {mode_name}")
            return True
        
        logger.info(f"Changing ASUS operation mode from {current_mode} to {mode_name}")
        
        # Try to set the mode using registry with different value names
        registry_values = ["PerformanceMode", "Profile", "GameProfile"]
        success = False
        
        # Try HKEY_CURRENT_USER first
        for registry_path in self.ASUS_REGISTRY_PATHS:
            for value_name in registry_values:
                try:
                    # First check if the key and value exist
                    try:
                        test_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
                        winreg.QueryValueEx(test_key, value_name)
                        winreg.CloseKey(test_key)
                        key_exists = True
                    except Exception:
                        key_exists = False
                    
                    # Only try to write if the key and value already exist
                    if key_exists:
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, mode_value)
                        winreg.CloseKey(key)
                        logger.info(f"Set ASUS operation mode to {mode_name} via HKCU\\{registry_path}\\{value_name}")
                        success = True
                        break
                except Exception as e:
                    logger.debug(f"Failed to set ASUS mode in HKCU\\{registry_path}\\{value_name}: {e}")
            
            if success:
                break
        
        # Try HKEY_LOCAL_MACHINE as fallback
        if not success:
            for registry_path in self.ASUS_REGISTRY_PATHS:
                for value_name in registry_values:
                    try:
                        # First check if the key and value exist
                        try:
                            test_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path)
                            winreg.QueryValueEx(test_key, value_name)
                            winreg.CloseKey(test_key)
                            key_exists = True
                        except Exception:
                            key_exists = False
                        
                        # Only try to write if the key and value already exist
                        if key_exists:
                            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_SET_VALUE)
                            winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, mode_value)
                            winreg.CloseKey(key)
                            logger.info(f"Set ASUS operation mode to {mode_name} via HKLM\\{registry_path}\\{value_name}")
                            success = True
                            break
                    except Exception as e:
                        logger.debug(f"Failed to set ASUS mode in HKLM\\{registry_path}\\{value_name}: {e}")
                
                if success:
                    break
        
        if success:
            # Verify the change
            new_mode = self._get_current_asus_mode()
            if new_mode == mode_name.lower():
                logger.info(f"Successfully set ASUS operation mode to {mode_name}")
                self.current_asus_mode = new_mode
                return True
            else:
                logger.warning(f"Failed to verify ASUS mode change. Expected {mode_name}, got {new_mode}")
        else:
            logger.error(f"Failed to set ASUS operation mode to {mode_name}")
            # Return True anyway to prevent blocking the power plan change
            return True
        
        return False
    
    def set_power_plan(self, plan_name):
        """
        Set the power plan using the standard Windows powercfg method and
        also set the corresponding ASUS operation mode.
        """
        if plan_name not in ["high_performance", "balanced", "power_saver"]:
            logger.warning(f"Unknown power plan name: {plan_name}")
            return
            
        # Always check current state before changing
        current_state = self._get_current_power_plan()
        
        if current_state == plan_name:
            logger.debug(f"Power plan already set to {plan_name}")
        else:
            logger.info(f"Changing power plan from {current_state} to {plan_name} using powercfg...")
            
            target_guid = None
            if plan_name == 'high_performance':
                target_guid = self.high_perf_guid
            elif plan_name == 'balanced':
                target_guid = self.balanced_guid
            elif plan_name == 'power_saver':
                target_guid = self.power_saver_guid
                
            if not target_guid or "placeholder" in target_guid.lower():
                logger.error(f"Invalid or placeholder GUID for {plan_name}: {target_guid}")
                return
                
            logger.info(f"Switching power plan to {plan_name} ({target_guid})")
            result = self._run_powercfg(["/setactive", target_guid])
            
            if result is not None:
                # Verify the change
                new_state = self._get_current_power_plan()
                if new_state == plan_name:
                     logger.info(f"Successfully set power plan to {plan_name}")
                     self.current_plan = plan_name
                else:
                     logger.error(f"Failed to verify power plan change. Expected {plan_name}, but got {new_state}.")
            else:
                logger.error(f"Failed to switch power plan to {plan_name} using powercfg.")
        
        # Also set the corresponding ASUS operation mode
        asus_mode = None
        if plan_name == 'high_performance':
            asus_mode = "turbo"
        elif plan_name == 'balanced':
            asus_mode = "performance"
        elif plan_name == 'power_saver':
            asus_mode = "silent"
        
        if asus_mode:
            logger.info(f"Setting corresponding ASUS operation mode: {asus_mode}")
            self.set_asus_operation_mode(asus_mode)
    
    def get_current_plan_name(self):
        """Get the current power plan name."""
        # Refresh the current plan state when requested
        self.current_plan = self._get_current_power_plan()
        return self.current_plan
        
    def get_current_asus_mode(self):
        """Get the current ASUS operation mode."""
        # Refresh the current ASUS mode when requested
        self.current_asus_mode = self._get_current_asus_mode()
        return self.current_asus_mode