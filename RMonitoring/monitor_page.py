# RMonitoring/monitor_page.py

import os
import re
import json
import time
from tkinter import Frame, Label, Button, Listbox, Scrollbar, Text, StringVar, filedialog, Toplevel, messagebox
from RMonitoring.real_time_monitor import RealTimeMonitor
from utils.tooltip import Tooltip

class MonitorPage(Frame):
    def __init__(self, root, scanner, switch_page_callback):
        super().__init__(root, bg="#009AA5")
        self.root = root
        self.scanner = scanner  # VWARScannerGUI instance
        self.switch_page_callback = switch_page_callback

        self.display_index_to_meta = {}
        self.monitoring_active = False
        self.scanner.monitoring_active = self.monitoring_active
        self.auto_scan_button_text = StringVar(value="Start Auto Scanning")

        self.setup_gui()

    def setup_gui(self):
        Button(self, text="Back", command=lambda: self.switch_page_callback("home"),
               bg="red", fg="white", font=("Inter", 12)).place(x=10, y=10, width=80, height=30)

        Label(self, text="Auto Scanning", font=("Inter", 16, "bold"),
              bg="#009AA5", fg="white").place(x=400, y=10)

        # Quarantine listbox
        Label(self, text="Quarantined Files", font=("Inter", 12, "bold"),
              bg="#009AA5", fg="white").place(x=20, y=60)
        self.scanner.quarantine_listbox = Listbox(self, font=("Inter", 11))
        self.scanner.quarantine_listbox.place(x=20, y=100, width=500, height=300)

        yscroll = Scrollbar(self, orient="vertical", command=self.scanner.quarantine_listbox.yview)
        yscroll.place(x=520, y=100, height=300)
        self.scanner.quarantine_listbox.config(yscrollcommand=yscroll.set)

        # Metadata text box
        Label(self, text="File Metadata", font=("Inter", 12, "bold"),
              bg="#009AA5", fg="white").place(x=550, y=60)
        self.scanner.detail_text = Text(self, font=("Inter", 11), wrap="word", state="disabled",
                                        bg="white", fg="black")
        self.scanner.detail_text.place(x=550, y=100, width=450, height=300)

        # Auto scan status
        self.scanner.auto_scan_status_label = Label(self, text="Status: Stopped",
                                                    font=("Inter", 12, "bold"), bg="#FFFFFF", fg="red")
        self.scanner.auto_scan_status_label.place(x=20, y=470)

        # Buttons
        Button(self, textvariable=self.auto_scan_button_text, command=self.toggle_monitoring,
               bg="#004953", fg="white", font=("Inter", 12, "bold")).place(x=20, y=420, width=200, height=40)
        Button(self, text="Delete Selected", command=self.delete_selected,
               bg="#B22222", fg="white", font=("Inter", 12)).place(x=250, y=470, width=180, height=40)
        Button(self, text="Restore from Backup", command=self.restore_quarantined_file,
               bg="blue", fg="white", font=("Inter", 12)).place(x=250, y=420, width=180, height=40)
        Button(self, text="Refresh", command=self.scanner.update_quarantine_listbox,
               bg="#006666", fg="white", font=("Inter", 12)).place(x=470, y=420, width=100, height=40)

        self.scanner.quarantine_listbox.bind("<<ListboxSelect>>", self.on_select)
        self.scanner.update_quarantine_listbox()

    def toggle_monitoring(self):
        if self.monitoring_active:
            self.scanner.monitor.stop()
            self.monitoring_active = False
            self.scanner.monitoring_active = False  # ✅ KEEP THIS IN SYNC
            self.auto_scan_button_text.set("Start Auto Scanning")
            self.scanner.auto_scan_status_label.config(text="Status: Stopped", fg="red")
        else:
            self.scanner.monitor = RealTimeMonitor(self.scanner, self.scanner.watch_paths)
            self.scanner.monitor.start()
            self.scanner.monitor.process_pending_files()
            self.monitoring_active = True
            self.scanner.monitoring_active = True  # ✅ KEEP THIS IN SYNC
            self.auto_scan_button_text.set("Stop Auto Scanning")
            self.scanner.auto_scan_status_label.config(text="Status: Running ●", fg="green")
            self.animate_status()


    def animate_status(self):
        if self.monitoring_active:
            current = self.scanner.auto_scan_status_label.cget("text")
            new_text = "Status: Running" if "●" in current else "Status: Running ●"
            self.scanner.auto_scan_status_label.config(text=new_text)
            self.root.after(500, self.animate_status)

    def on_select(self, event):
        index = self.scanner.quarantine_listbox.curselection()
        if not index:
            return
        meta_path = self.scanner.display_index_to_meta.get(index[0])
        if not meta_path or not os.path.exists(meta_path):
            return
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            detail_text = (
                f"Original Path:\n{metadata.get('original_path', 'Unknown')}\n\n"
                f"Quarantined At:\n{metadata.get('timestamp', 'Unknown')}\n\n"
                f"Matched Rules:\n{', '.join(metadata.get('matched_rules', []))}"
            )
        except Exception as e:
            detail_text = f"Failed to load metadata:\n{e}"
        self.scanner.detail_text.config(state="normal")
        self.scanner.detail_text.delete("1.0", "end")
        self.scanner.detail_text.insert("end", detail_text)
        self.scanner.detail_text.config(state="disabled")

    # def delete_selected(self):
    #     index = self.scanner.quarantine_listbox.curselection()
    #     if not index:
    #         return
    #     selected = self.scanner.quarantine_listbox.get(index)
    #     match = re.search(r"→ From:\s*(.+)", selected)
    #     if not match:
    #         messagebox.showerror("Error", "Could not parse original path.")
    #         return
    #     file_path = match.group(1)
    #     fname = os.path.basename(file_path)
    #     for file in os.listdir("quarantine"):
    #         if file.startswith(fname) and file.endswith(".quarantined"):
    #             qpath = os.path.join("quarantine", file)
    #             mpath = qpath + ".meta"
    #             try:
    #                 if os.path.exists(qpath): os.remove(qpath)
    #                 if os.path.exists(mpath): os.remove(mpath)
    #                 self.scanner.quarantine_listbox.delete(index)
    #                 self.scanner.detail_text.config(state="normal")
    #                 self.scanner.detail_text.delete("1.0", "end")
    #                 self.scanner.detail_text.config(state="disabled")
    #                 self.scanner.update_quarantine_listbox()
    #             except Exception as e:
    #                 print(f"[ERROR] Delete failed: {e}")
    #             break

    def delete_selected(self):
        index = self.scanner.quarantine_listbox.curselection()
        if not index:
            return
        index = index[0]

        # ✅ Use stored meta path instead of parsing text
        meta_path = self.scanner.display_index_to_meta.get(index)
        if not meta_path:
            messagebox.showerror("Error", "Metadata not found for selected file.")
            return

        qpath = meta_path.replace(".meta", "")
        
        try:
            if os.path.exists(qpath): os.remove(qpath)
            if os.path.exists(meta_path): os.remove(meta_path)

            self.scanner.quarantine_listbox.delete(index)
            self.scanner.detail_text.config(state="normal")
            self.scanner.detail_text.delete("1.0", "end")
            self.scanner.detail_text.config(state="disabled")
            self.scanner.update_quarantine_listbox()
            print(f"[INFO] Deleted {qpath} and metadata.")
        except Exception as e:
            print(f"[ERROR] Delete failed: {e}")



    def restore_quarantined_file(self):
        index = self.scanner.quarantine_listbox.curselection()
        if not index:
            messagebox.showwarning("No Selection", "Please select a file.")
            return
        text = self.scanner.quarantine_listbox.get(index)
        match = re.search(r"→ From:\s*(.+)", text)
        if not match:
            messagebox.showerror("Error", "Could not parse original path.")
            return
        original_path = match.group(1)
        fname = os.path.basename(original_path)

        backup_root = filedialog.askdirectory(title="Select VWARbackup Folder")
        if not backup_root or not backup_root.endswith("VWARbackup"):
            messagebox.showerror("Error", "Invalid backup folder.")
            return

        found = []
        for root, _, files in os.walk(backup_root):
            for file in files:
                if file == fname + ".backup":
                    found.append(os.path.join(root, file))
        if not found:
            messagebox.showinfo("Not Found", "No backup file found.")
            return

        selected = found[0]
        if len(found) > 1:
            top = Toplevel(self.root)
            top.title("Choose Backup")
            listbox = Listbox(top, width=80)
            listbox.pack()
            for f in found:
                listbox.insert("end", f)
            def confirm():
                nonlocal selected
                if listbox.curselection():
                    selected = listbox.get(listbox.curselection()[0])
                    top.destroy()
            Button(top, text="Restore", command=confirm).pack()
            top.transient(self.root)
            top.grab_set()
            self.root.wait_window(top)

        try:
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            import shutil
            shutil.copy2(selected, original_path)
            messagebox.showinfo("Restored", f"Restored to:\n{original_path}")
        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))

    def add_to_quarantine_listbox(self, file_path, meta_path, matched_rules):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file_name = os.path.basename(file_path)
        display_text = f"File: {file_name}\n→ From: {file_path}\n→ Matched: {', '.join(matched_rules)}\n→ Time: {timestamp}"
        self.scanner.quarantine_listbox.insert("end", display_text)
        self.scanner.display_index_to_meta[self.scanner.quarantine_listbox.size() - 1] = meta_path
