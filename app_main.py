import os
import json

from tkinter import Tk, Frame, Label, Button
from config import ICON_PATH, CURRENT_VERSION, ACTIVATION_FILE, QUARANTINE_FOLDER
from Scanning.scan_page import ScanPage
from Backup.main_backup_page import BackupMainPage
from Backup.backup_page import ManualBackupPage
from Backup.restore_page import RestoreBackupPage
from Backup.auto_backup_page import AutoBackupPage
from Backup.auto_backup import AutoBackupScheduler
from RMonitoring.monitor_page import MonitorPage


class VWARScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VWAR Scanner")
        self.root.geometry("1043x722")
        self.root.configure(bg="#009AA5")
        self.root.iconbitmap(ICON_PATH)
        AutoBackupScheduler().start()

        # Shared state used by all pages
        self.pages = {}
        self.rules = None
        self.target_path = None
        self.stop_scan = False
        self.selected_files = []
        self.rule_folder = os.path.join(os.getcwd(), "assets", "yara")
        os.makedirs(self.rule_folder, exist_ok=True)

        self.quarantine_folder = QUARANTINE_FOLDER
        os.makedirs(self.quarantine_folder, exist_ok=True)

        self.activated_user = "Unknown"
        self.valid_till = "Unknown"
        self.load_activation_info()
        self.watch_paths = self.get_all_accessible_drives()

        # Build all GUI pages
        self.create_home_page()
        self.pages["scan"] = ScanPage(self.root, self.show_page)
        self.pages["backup"] = BackupMainPage(self.root, self.show_page)
        self.pages["manual_backup"] = ManualBackupPage(self.root, self.show_page)
        self.pages["restore_backup"] = RestoreBackupPage(self.root, self.show_page)
        self.pages["auto_backup"] = AutoBackupPage(self.root, self.show_page)
        self.pages["monitor"] = MonitorPage(self.root, self, self.show_page)


        # Show home first
        self.show_page("home")

        # Cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_home_page(self):
        frame = Frame(self.root, bg="#009AA5")
        self.pages["home"] = frame

        Label(frame, text="VWAR Scanner", font=("Arial", 24), bg="#009AA5", fg="white").place(x=420, y=30)

        Button(frame, text="Scan Files", command=lambda: self.show_page("scan"),
               bg="blue", fg="white", font=("Arial", 16)).place(x=420, y=150, width=200, height=50)

        Button(frame, text="Backup", command=lambda: self.show_page("backup"),
               bg="orange", fg="white", font=("Arial", 16)).place(x=420, y=230, width=200, height=50)

        Button(frame, text="Auto Scan", command=lambda: self.show_page("monitor"),
               bg="green", fg="white", font=("Arial", 16)).place(x=420, y=310, width=200, height=50)

        Label(frame, text=f"User: {self.activated_user}", font=("Arial", 12),
              bg="white", fg="black").place(x=420, y=400)

        Label(frame, text=f"Valid Till: {self.valid_till}", font=("Arial", 12),
              bg="white", fg="black").place(x=420, y=430)

        Label(frame, text=f"Version: {CURRENT_VERSION}", font=("Arial", 10),
              bg="#009AA5", fg="white").place(x=10, y=680)

    # def show_page(self, name):
    #     """Switch to the specified page by name."""
    #     for page in self.pages.values():
    #         page.place_forget()
    #     if name in self.pages:
    #         self.pages[name].place(x=0, y=0, width=1043, height=722)
    
    def show_page(self, name):
        for page in self.pages.values():
            page.place_forget()

        if name not in self.pages:
            print(f"[ERROR] Page '{name}' not found.")
            return

        # ✅ This ensures page appears
        self.pages[name].place(x=0, y=0, width=1043, height=722)


    def load_activation_info(self):
        """Reads activation.json and sets user info."""
        try:
            with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.activated_user = data.get("username", "Unknown")
                self.valid_till = data.get("valid_till", "Unknown")
        except Exception:
            pass

    def on_close(self):
        """Stops monitoring/backup if running, exits app cleanly."""
        if hasattr(self, "real_time_monitor"):
            self.real_time_monitor.stop()
        if hasattr(self, "auto_backup"):
            self.auto_backup.stop()
        self.root.destroy()
 
    def update_quarantine_listbox(self):
        """Refresh the quarantine list with current files."""
        self.quarantine_listbox.delete(0, "end")
        self.display_index_to_meta = {}

        if not os.path.exists(self.quarantine_folder):
            return

        index = 0
        for file in os.listdir(self.quarantine_folder):
            if file.endswith(".quarantined"):
                base_name = file[:-12]  # Remove '.quarantined'
                meta_file = os.path.join(self.quarantine_folder, file + ".meta")
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        original_path = meta.get("original_path", "Unknown")
                        display = f"File: {base_name}\n→ From: {original_path}"
                        self.quarantine_listbox.insert("end", display)
                        self.display_index_to_meta[index] = meta_file
                        index += 1
                    except Exception as e:
                        print(f"[WARNING] Failed to load metadata for {file}: {e}")


    def get_all_accessible_drives(self):
        from string import ascii_uppercase
        drives = [f"{d}:/" for d in ascii_uppercase if os.path.exists(f"{d}:/")]
        drives.append(os.path.expanduser("~"))  # Include user home folder
        return list(set(drives))
