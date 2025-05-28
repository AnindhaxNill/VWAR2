import os
import sys
import ctypes
import tkinter as tk
from activation.license_utils import is_activated
from activation.gui import show_activation_window
from app_main import VWARScannerGUI
from utils.update_checker import check_for_updates

def is_admin():
    """
    Check if the program is running with administrator privileges.
    Returns True if yes, False otherwise.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """
    Relaunch the script with administrator privileges if not already.
    """
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)


def main():
    """
    Main entry point of the VWAR Scanner application.
    """
    # Step 1: Elevate to admin
    # if not is_admin():
    #     print("[INFO] Not running as admin. Relaunching...")
    #     run_as_admin()
    #     return

    # Step 2: Check activation
    # if not is_activated():
    #     print("[INFO] System not activated. Launching activation window...")
    #     show_activation_window()
    #     return
    
    activated, reason = is_activated()
    if not activated:
        print(f"[INFO] Activation check failed: {reason}")
        show_activation_window(reason=reason)
        return

    check_for_updates()

    # Step 3: Launch main GUI
    print("[INFO] Launching VWAR Scanner GUI...")
    root = tk.Tk()
    app = VWARScannerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
