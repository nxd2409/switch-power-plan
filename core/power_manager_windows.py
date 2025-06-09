import subprocess
import logging
import ctypes
import time

logger = logging.getLogger(__name__)

class PowerManagerWindows: 
    def __init__(self, high_perf_guid, balanced_guid, power_saver_guid, turbo_guid=None):
        if not self._is_admin():
            logger.error("Administrator privileges required!")
            raise PermissionError("This application must be run as administrator")
            
        self.high_perf_guid = high_perf_guid
        self.balanced_guid = balanced_guid
        self.power_saver_guid = power_saver_guid
        self.turbo_guid = turbo_guid
        self.current_plan = self._get_current_power_plan()

        self._validate_guids()
        logger.info(f"PowerManagerWindows initialized. Current plan: {self.current_plan}")
        
    def _is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            logger.error(f"Error checking admin rights: {e}")
            return False
            
    def _validate_guids(self):
        if "placeholder" in self.high_perf_guid.lower():
            logger.error("High Performance GUID is a placeholder!")
        if "placeholder" in self.balanced_guid.lower():
            logger.error("Balanced GUID is a placeholder!")
        if "placeholder" in self.power_saver_guid.lower():
            logger.error("Power Saver GUID is a placeholder!")
        if self.turbo_guid and "placeholder" in self.turbo_guid.lower():
            logger.error("Turbo GUID is a placeholder!")
            
    def _run_powercfg(self, args):
        if not self._is_admin():
            logger.error("Administrator privileges required!")
            return None
            
        try:
            cmd = ["powercfg"] + args
            logger.debug(f"Running: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, 
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                if result.stdout:
                    logger.debug(f"powercfg output: {result.stdout.strip()}")
                return result.stdout.strip()
            else:
                logger.error(f"powercfg error: {result.stderr.strip()}")
                return None
                
        except Exception as e:
            logger.error(f"Error running powercfg: {e}")
            return None
    
    def _get_current_power_plan(self):
        output = self._run_powercfg(["/getactivescheme"])
        if not output:
            return None
            
        try:
            guid = output.split("GUID: ")[1].split(" ")[0].strip()

            if guid.lower() == self.high_perf_guid.lower():
                return "high_performance"
            elif guid.lower() == self.balanced_guid.lower():
                return "balanced"
            elif guid.lower() == self.power_saver_guid.lower():
                return "power_saver"
            elif self.turbo_guid and guid.lower() == self.turbo_guid.lower():
                return "turbo"
            else:
                plan_name = output.split("(")[1].split(")")[0].strip()
                logger.warning(f"Unknown power plan: {plan_name} ({guid})")
                return None
        except Exception as e:
            logger.error(f"Error parsing power plan: {e}")
            return None
            
    def set_power_plan(self, plan_name):
        if plan_name not in ["high_performance", "balanced", "power_saver", "turbo"]:
            logger.error(f"Unknown power plan: {plan_name}")
            return False

        current_plan = self._get_current_power_plan()
        if current_plan == plan_name:
            logger.debug(f"Already in {plan_name} mode")
            return True

        target_guid = None
        if plan_name == "high_performance":
            target_guid = self.high_perf_guid
        elif plan_name == "balanced":
            target_guid = self.balanced_guid
        elif plan_name == "power_saver":
            target_guid = self.power_saver_guid
        elif plan_name == "turbo" and self.turbo_guid:
            target_guid = self.turbo_guid
            
        if not target_guid or "placeholder" in target_guid.lower():
            logger.error(f"Invalid GUID for {plan_name}")
            return False

        logger.info(f"Changing power plan from {current_plan} to {plan_name}")
        result = self._run_powercfg(["/setactive", target_guid])
        
        if result is not None:
            time.sleep(0.5) 
            new_plan = self._get_current_power_plan()
            if new_plan == plan_name:
                logger.info(f"Successfully changed to {plan_name}")
                self.current_plan = plan_name
                return True
            else:
                logger.error(f"Failed to verify change. Got {new_plan}")
                return False
        else:
            logger.error(f"Failed to set {plan_name}")
            return False
    
    def get_current_plan_name(self):
        self.current_plan = self._get_current_power_plan()
        return self.current_plan