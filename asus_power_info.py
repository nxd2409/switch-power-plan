import os
import sys
import subprocess
import winreg
import ctypes
import platform
import time

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def run_command(cmd):
    """Run a command and return its output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"

def check_system_info():
    """Check system information."""
    print_header("SYSTEM INFORMATION")
    print(f"Machine: {platform.machine()}")
    print(f"Node: {platform.node()}")
    print(f"System: {platform.system()}")
    print(f"Platform: {platform.platform()}")
    print(f"Processor: {platform.processor()}")
    
    # Check if it's likely an ASUS system
    is_asus = any(brand in platform.node().upper() for brand in ["ASUS", "ROG", "TUF", "FLOW"])
    print(f"ASUS laptop detected: {is_asus}")
    
    # Admin check
    print(f"Running with admin privileges: {is_admin()}")

def check_power_plans():
    """Check available power plans using powercfg."""
    print_header("WINDOWS POWER PLANS")
    print(run_command("powercfg /list"))
    
    print("\nACTIVE POWER SCHEME:")
    print(run_command("powercfg /getactivescheme"))

def check_asus_registry():
    """Check ASUS-related registry entries."""
    print_header("ASUS REGISTRY SETTINGS")
    
    registry_paths = [
        r"SOFTWARE\ASUS\ASUS System Control Interface",
        r"SOFTWARE\ASUS\ArmouryDevice\AirController",
        r"SOFTWARE\ASUS\ASUS Power Mode",
        r"SOFTWARE\ASUS\ArmouryDevice\PerformanceMode"
    ]
    
    found_any = False
    
    for path in registry_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
            print(f"\nPath: {path}")
            
            # Try to enumerate values
            i = 0
            while True:
                try:
                    name, value, type_id = winreg.EnumValue(key, i)
                    if isinstance(value, bytes):
                        value = value.hex()
                    print(f"  {name} = {value} (Type: {type_id})")
                    i += 1
                    found_any = True
                except OSError:
                    break
            
            winreg.CloseKey(key)
        except FileNotFoundError:
            print(f"Path not found: {path}")
        except Exception as e:
            print(f"Error with {path}: {e}")
    
    if not found_any:
        print("No ASUS registry settings found. This may not be an ASUS system or the registry structure differs.")

def check_asus_software():
    """Check for installed ASUS software."""
    print_header("ASUS SOFTWARE")
    
    asus_paths = [
        r"C:\Program Files (x86)\ASUS",
        r"C:\Program Files\ASUS",
        r"C:\Program Files (x86)\ASUS\ArmouryCrate",
        r"C:\Program Files\ASUS\ArmouryCrate"
    ]
    
    for path in asus_paths:
        if os.path.exists(path):
            print(f"Found ASUS directory: {path}")
            # List main executables
            exe_files = []
            try:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(".exe") and any(name in file.lower() for name in ["crate", "armour", "mode", "control"]):
                            exe_files.append(os.path.join(root, file))
                
                for exe in exe_files[:10]:  # Show at most 10 executables
                    print(f"  {exe}")
                
                if len(exe_files) > 10:
                    print(f"  ... and {len(exe_files) - 10} more")
            except Exception as e:
                print(f"  Error listing files: {e}")
        else:
            print(f"Not found: {path}")

def test_power_mode_change():
    """Try to change power modes using different methods."""
    if not is_admin():
        print("\nWARNING: Not running as admin. Mode changes may fail.")
    
    print_header("POWER MODE CHANGE TESTS")
    print("This will attempt to switch power modes using different methods.")
    print("Watch your system's power mode indicators (if any) to see if changes take effect.")
    print("Press Ctrl+C at any time to cancel.")
    
    try:
        # Method 1: Standard powercfg
        print("\nTesting Windows powercfg method...")
        
        # Get available power schemes
        schemes_output = run_command("powercfg /list")
        schemes = []
        
        for line in schemes_output.splitlines():
            if "Power Scheme GUID:" in line:
                try:
                    guid = line.split("GUID:")[1].split(" ")[1].strip()
                    name = line.split("(")[1].split(")")[0].strip()
                    schemes.append((guid, name))
                except:
                    pass
        
        if not schemes:
            print("No power schemes found!")
        else:
            for guid, name in schemes:
                print(f"Setting power scheme to {name}...")
                result = run_command(f"powercfg /setactive {guid}")
                print(f"Result: {result or 'Success'}")
                print("Wait 3 seconds to observe changes...")
                time.sleep(3)
        
        # Method 2: ASUS registry method
        print("\nTesting ASUS registry method...")
        registry_paths = [
            r"SOFTWARE\ASUS\ASUS System Control Interface",
            r"SOFTWARE\ASUS\ASUS Power Mode"
        ]
        
        # Values to try: 0=Silent, 1=Balanced/Performance, 2=Turbo
        for mode_value in [0, 1, 2]:
            mode_names = {0: "Silent", 1: "Performance", 2: "Turbo"}
            mode_name = mode_names.get(mode_value, f"Mode {mode_value}")
            
            print(f"Attempting to set {mode_name} mode...")
            
            for path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "PerformanceMode", 0, winreg.REG_DWORD, mode_value)
                    winreg.CloseKey(key)
                    print(f"Set value in {path}")
                    print("Wait 3 seconds to observe changes...")
                    time.sleep(3)
                    break
                except Exception as e:
                    print(f"Failed for {path}: {e}")
    
    except KeyboardInterrupt:
        print("\nTest canceled by user.")
    except Exception as e:
        print(f"\nError during testing: {e}")

def main():
    """Main function to run all checks."""
    print("ASUS Power Information Utility")
    print("This tool will check your system's power configuration")
    print("and help identify how to control ASUS-specific power modes.")
    
    check_system_info()
    check_power_plans()
    check_asus_registry()
    check_asus_software()
    
    # Ask if user wants to test power mode changes
    print_header("POWER MODE CHANGE TEST")
    print("Warning: This will attempt to change your system's power modes.")
    try:
        choice = input("Do you want to run power mode change tests? (y/n): ").strip().lower()
        if choice == 'y':
            test_power_mode_change()
    except KeyboardInterrupt:
        print("\nCanceled.")
    
    print_header("COMPLETED")
    print("This information can help you understand how your system's power modes work.")
    print("Add the appropriate values to your Smart Power Manager configuration.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 