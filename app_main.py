import os
import json

from tkinter import Tk, Frame, Label, Button,LabelFrame
from config import ICON_PATH, ACTIVATION_FILE, QUARANTINE_FOLDER
from Scanning.scan_page import ScanPage
from Backup.main_backup_page import BackupMainPage
from Backup.backup_page import ManualBackupPage
from Backup.restore_page import RestoreBackupPage
from Backup.auto_backup_page import AutoBackupPage
from Backup.auto_backup import AutoBackupScheduler
from RMonitoring.monitor_page import MonitorPage
from utils.update_checker import check_for_updates,CURRENT_VERSION,up_to


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
        # Force start Real-Time Monitoring at launch
        try:
            self.pages["monitor"].toggle_monitoring()
            
            print("[INFO] Auto-started Real-Time Monitoring from app_main.py")
        except Exception as e:
            print(f"[ERROR] Could not auto-start Real-Time Monitoring: {e}")



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
        
        
        self.home_scan_status_label = Label(frame, text="Status: Running ●",
                                            font=("Arial", 16, "bold"),
                                            bg="white", fg="green")
        self.home_scan_status_label.place(x=630, y=320)  # Adjust coordinates as needed

        Label(frame, text=f"User: {self.activated_user}", font=("Arial", 12),
              bg="white", fg="black").place(x=420, y=400)

        Label(frame, text=f"Valid Till: {self.valid_till}", font=("Arial", 12),
              bg="white", fg="black").place(x=420, y=430)

        # Label(frame, text=f"Version: {CURRENT_VERSION}", font=("Arial", 10),
        #       bg="#009AA5", fg="white").place(x=10, y=680)
        
    # 🔔 Update status label
    
        # print(check_for_updates())
        if up_to() == 1:
            # Label(frame, text="🔺 Update Available", font=("Arial", 10), bg="white", fg="yellow").place(x=20, y=10)
            Button(frame, text="🔺 Update Available", command=check_for_updates,
               bg="white", fg="yellow", font=("Arial", 10)).place(x=20, y=10)
        elif  up_to() != 1:
            Label(frame, text="✅ Up to Date", font=("Arial", 10), bg="white", fg="green").place(x=20, y=10)
          
          
        contact_frame = LabelFrame(frame, text="About / Contact Us", bg="#009AA5", fg="white", font=("Arial", 12, "bold"), padx=10, pady=10)
        contact_frame.place(x=20, y=550, width=600, height=170)   
        Label(contact_frame, text=f"Version: {CURRENT_VERSION}", bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")
        Label(contact_frame, text="Developer: Bitss.fr", bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")
        Label(contact_frame, text="Email: Bitss.fr", bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")
        Label(contact_frame, text="Website: www.Bitss.fr", bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")
        Label(contact_frame, text="Support: Bitss.fr", bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")                                                       
        
        
        
       
        self.animate_home_status()




    def animate_home_status(self):
        if getattr(self, "pages", None) and "monitor" in self.pages:
            monitor_page = self.pages["monitor"]
            if getattr(monitor_page, "monitoring_active", False):
                current = self.home_scan_status_label.cget("text")
                new_text = "Status: Running" if "●" in current else "Status: Running ●"
                self.home_scan_status_label.config(text=new_text)
            else:
                self.home_scan_status_label.config(text="Status: Stopped", fg="red")
        self.root.after(500, self.animate_home_status)

   
    def show_page(self, name):
        print(f"[DEBUG] Switching to page: {name}")

        # Hide all other pages
        for page in self.pages.values():
            page.place_forget()

        if name not in self.pages:
            print(f"[ERROR] Page '{name}' not found.")
            return

        # Show the requested page
        self.pages[name].place(x=0, y=0, width=1043, height=722)

        # ✅ If Monitor page is shown, auto-refresh list
        if name == "monitor":
            try:
                self.pages["monitor"].update_quarantine_listbox()
                print("[DEBUG] Auto-refreshed quarantine list in Monitor page.")
            except Exception as e:
                print(f"[ERROR] Failed to refresh Monitor page: {e}")



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
 
    # def update_quarantine_listbox(self):
    #     """Refresh the quarantine list with current files."""
    #     self.quarantine_listbox.delete(0, "end")
    #     self.display_index_to_meta = {}

    #     if not os.path.exists(self.quarantine_folder):
    #         return

    #     index = 0
    #     for file in os.listdir(self.quarantine_folder):
    #         if file.endswith(".quarantined"):
    #             base_name = file[:-12]  # Remove '.quarantined'
    #             meta_file = os.path.join(self.quarantine_folder, file + ".meta")
    #             if os.path.exists(meta_file):
    #                 try:
    #                     with open(meta_file, "r", encoding="utf-8") as f:
    #                         meta = json.load(f)
    #                     original_path = meta.get("original_path", "Unknown")
    #                     display = f"File: {base_name}\n→ From: {original_path}"
    #                     self.quarantine_listbox.insert("end", display)
    #                     self.display_index_to_meta[index] = meta_file
    #                     index += 1
    #                 except Exception as e:
    #                     print(f"[WARNING] Failed to load metadata for {file}: {e}")





    def get_all_accessible_drives(self):
        from string import ascii_uppercase
        drives = [f"{d}:/" for d in ascii_uppercase if os.path.exists(f"{d}:/")]
        drives.append(os.path.expanduser("~"))  # Include user home folder
        return list(set(drives))

