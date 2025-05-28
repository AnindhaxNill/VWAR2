

##############################################################################################


import os, threading, base64, time, shutil, traceback
from tkinter import Frame, Button, Label, Text, Canvas, filedialog
from tkinter.ttk import Progressbar

from Scanning.yara_engine import fetch_and_generate_yara_rules, compile_yara_rules
from Scanning.quarantine import quarantine_file
from utils.tooltip import Tooltip
from utils.logger import log_message
import yara
import os
from datetime import datetime
import shutil
import json
from utils.logger import log_message
from Scanning.scanner_core import scan_file_for_realtime 


class ScanPage(Frame):
    def __init__(self, root, switch_page_callback):
        super().__init__(root, bg="#009AA5")
        self.root = root
        self.switch_page_callback = switch_page_callback

        self.target_path = None
        self.rules = None
        self.stop_scan = False

        self.build_ui()
        fetch_and_generate_yara_rules(self.log)
        self.root.after(100, self.load_rules)

    def build_ui(self):
        # Back Button
        back_btn = Button(self, text="← Back", command=lambda: self.switch_page_callback("home"),
                          bg="gold", fg="white", font=("Inter", 12))
        back_btn.place(x=10, y=10, width=80, height=30)

        # LOAD TEXT log box
        self.LOAD_TEXT = Text(self, bg="#D9D9D9", fg="black", wrap="word")
        self.LOAD_TEXT.place(x=302, y=10, width=600, height=100)

        # Select File Button
        Button(self, text="Select Target File", command=self.select_file).place(x=302, y=139, width=125, height=40)
        label_file = Label(self, text="?", bg="#009AA5", fg="white", font=("Arial", 12, "bold"))
        label_file.place(x=432, y=139)
        Tooltip(label_file, "Choose a file to scan with YARA rules.")

        # Select Folder Button
        Button(self, text="Select Target Folder", command=self.select_folder).place(x=302, y=195, width=125, height=40)
        label_folder = Label(self, text="?", bg="#009AA5", fg="white", font=("Arial", 12, "bold"))
        label_folder.place(x=432, y=195)
        Tooltip(label_folder, "Choose a folder to scan recursively")

        # Start Scan Button
        Button(self, text="Scan", command=self.start_scan_thread, bg="green", fg="white").place(x=485, y=150, width=73, height=25)
        label_start = Label(self, text="?", bg="#009AA5", fg="white", font=("Arial", 12, "bold"))
        label_start.place(x=570, y=150)
        Tooltip(label_start, "Start the scanning immediately.")

        # Stop Button
        Button(self, text="Stop", command=self.stop_scan_thread, bg="red", fg="white").place(x=485, y=195, width=73, height=25)
        label_stop = Label(self, text="?", bg="#009AA5", fg="white", font=("Arial", 12, "bold"))
        label_stop.place(x=570, y=195)
        Tooltip(label_stop, "Stop the scanning immediately.")

        # Quarantine Navigation Button
        Button(self, text="Show Quarantined Files", command=lambda: self.switch_page_callback("monitor"),
               bg="purple", fg="white", font=("Inter", 12)).place(x=700, y=195, width=200, height=40)
        label_quarantine = Label(self, text="?", bg="#009AA5", fg="white", font=("Arial", 12, "bold"))
        label_quarantine.place(x=910, y=195)
        Tooltip(label_quarantine, "View files moved to quarantine after detection")

        # Progress bar
        self.progress_label = Label(self, text="PROGRESS : 0%", bg="#12e012", fg="#000000", font=("Inter", 12))
        self.progress_label.place(x=476, y=311)

        self.progress = Progressbar(self, orient="horizontal", length=350, mode="determinate")
        self.progress.place(x=354, y=350)

        # Matched Files section
        matched_canvas = Canvas(self, bg="#AE0505", height=54, width=485, bd=0, highlightthickness=0, relief="ridge")
        matched_canvas.place(x=0, y=432)
        matched_canvas.create_text(164, 15, anchor="nw", text="MATCHED FILES", fill="#FFFFFF", font=("Inter", 20))

        self.matched_text = Text(self, bg="#F0CDCD", fg="#000000", wrap="word")
        self.matched_text.place(x=0, y=488, width=485, height=232)

        # Tested Files section
        tested_canvas = Canvas(self, bg="#0A8D05", height=54, width=485, bd=0, highlightthickness=0, relief="ridge")
        tested_canvas.place(x=557, y=432)
        tested_canvas.create_text(164, 15, anchor="nw", text="TESTED FILES", fill="#FFFFFF", font=("Inter", 20))

        self.tested_text = Text(self, bg="#B6F7AD", fg="#000000", wrap="word")
        self.tested_text.place(x=557, y=488, width=485, height=232)

    def log(self, msg, target="load"):
        log_message(msg)
        if target == "load":
            self.LOAD_TEXT.insert("end", msg + "\n")
        elif target == "matched":
            self.matched_text.insert("end", msg + "\n")
        elif target == "tested":
            self.tested_text.insert("end", msg + "\n")

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.target_path = path
            self.LOAD_TEXT.delete("1.0", "end")
            self.log(f"[INFO] Selected file: {path}", "load")

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.target_path = path
            self.LOAD_TEXT.delete("1.0", "end")
            self.log(f"[INFO] Selected folder: {path}", "load")

    def start_scan_thread(self):
        self.stop_scan = False
        thread = threading.Thread(target=self.scan, daemon=True)
        thread.start()

    def stop_scan_thread(self):
        self.stop_scan = True
        self.log("[INFO] Scan stop requested.", "load")

    def load_rules(self):
        self.rules = compile_yara_rules(log_func=self.log)

    def scan(self):
        if not self.rules:
            self.log("[ERROR] No YARA rules loaded.", "load")
            return
        if not self.target_path:
            self.log("[ERROR] No target path selected.", "load")
            return

        self.matched_text.delete("1.0", "end")
        self.tested_text.delete("1.0", "end")

        if os.path.isfile(self.target_path):
            self.scan_file(self.target_path)
        elif os.path.isdir(self.target_path):
            self.scan_directory(self.target_path)

        self.progress.stop()
        self.progress_label.config(text="Scan Complete!")

    def scan_directory(self, directory):
        files = []
        for root, _, filenames in os.walk(directory):
            for f in filenames:
                files.append(os.path.join(root, f))

        total = len(files)
        self.progress["maximum"] = total
        self.progress["value"] = 0

        for i, file_path in enumerate(files, 1):
            if self.stop_scan:
                break
            self.scan_file(file_path)
            self.progress["value"] = i
            percent = int((i / total) * 100)
            self.progress_label.config(text=f"PROGRESS : {percent}%")
            self.root.update_idletasks()

    # def scan_file(self, path):
    #     try:
    #         matches = self.rules.match(path, timeout=60)
    #         self.log(path, "tested")
    #         if matches:
    #             rule = matches[0].rule
    #             self.log(f"[MATCH] {path} => Rule: {rule}", "matched")
    #             quarantine_file(path, matched_rules=[rule])
    #     except Exception as e:
    #         self.log(f"[ERROR] Failed to scan {path}:\n{traceback.format_exc()}", "tested")

    def scan_file(self, path):
        self.log(path, "tested")
        matched, rule, qpath, meta_path = scan_file_for_realtime(path)
        if matched:
            self.log(f"[MATCH] {path} => Rule: {rule}", "matched")



    # def scan_file(self, file_path):
    #     """Scan a single file using YARA rules and quarantine if matched."""
    #     print(f"[DEBUG] Scanning file: {file_path}")
    #     try:
    #         with open(file_path, "rb"):
    #             pass
    #     except Exception:
    #         print(f"[WARNING] Cannot open file: {file_path}")
    #         return

    #     # Compile rules
    #     rule_paths = {}
    #     yara_dir = os.path.join("assets", "yara")
    #     for category in os.listdir(yara_dir):
    #         cat_path = os.path.join(yara_dir, category)
    #         for rule in os.listdir(cat_path):
    #             if rule.endswith(".yar") or rule.endswith(".yara"):
    #                 key = f"{category}_{rule}"
    #                 rule_paths[key] = os.path.join(cat_path, rule)

    #     try:
    #         rules = yara.compile(filepaths=rule_paths)
    #         matches = rules.match(filepath=file_path)
    #     except Exception as e:
    #         print(f"[ERROR] YARA scan failed: {e}")
    #         return

    #     if matches:
    #         log_message(f"[MATCH] {file_path} matched {matches}")
    #         self.quarantine_file(file_path, [str(m) for m in matches])
    #         self.update_quarantine_listbox()
    #         self.notify_threat_detected(file_path, matches)
