
import os
import time
import threading
import getpass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from Scanning.scanner_core import scan_file_for_realtime


def is_file_ready(path):
    try:
        if not os.path.exists(path):
            return False
        if os.path.getsize(path) == 0:
            return False
        with open(path, "rb") as f:
            chunk = f.read(4096)
            return bool(chunk)
    except:
        return False


class RealTimeMonitor(FileSystemEventHandler):
    def __init__(self, gui, watch_paths):
        self.gui = gui
        self.watch_paths = watch_paths if isinstance(watch_paths, list) else [watch_paths]
        self.observer = Observer()
        self.recent_events = {}  # path -> timestamp
        self.pending_scan_files = set()
        self.already_scanned = set()

        user = getpass.getuser()

        self.excluded_folders = [
            os.path.join("C:\\Users", user, "AppData"),
            os.path.join("C:\\Windows"),
            os.path.join("C:\\$Recycle.Bin"),
            os.path.join("C:\\ProgramData"),
            "System Volume Information",
            os.path.join(os.getcwd(), "quarantine"),
            os.path.join(os.getcwd(), "backup"),
            os.path.join(os.getcwd(), "yara"),
            os.path.join(os.getcwd(), "VWARbackup"),
        ]

        self.excluded_extensions = (".tmp", ".log", ".lock", ".crdownload", ".part", ".ds_store", "thumbs.db")
        self.excluded_prefixes = ("~$",)

    def start(self):
        print("[DEBUG] Starting RealTimeMonitor:")
        for path in self.watch_paths:
            print(f"  ➤ Watching: {path}")
            try:
                self.observer.schedule(self, path=path, recursive=True)
            except Exception as e:
                print(f"[ERROR] Failed to watch {path}: {e}")
        self.observer.start()

    def stop(self):
        print("[INFO] Stopping RealTimeMonitor.")
        self.observer.stop()
        self.observer.join()

    def is_excluded(self, path):
        path = os.path.abspath(path).lower()
        for folder in self.excluded_folders:
            folder = os.path.abspath(folder).lower()
            if folder in path:
                return True
        return False

    def is_excluded_file(self, path):
        filename = os.path.basename(path).lower()
        if filename.endswith(self.excluded_extensions) or filename.startswith(self.excluded_prefixes):
            return True
        try:
            if os.path.exists(path) and os.path.getsize(path) == 0:
                return True
        except:
            return True
        return False

    def on_created(self, event):
        if not event.is_directory:
            self._handle_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_event(event.src_path)



    def _handle_event(self, path):
        path = os.path.abspath(path).replace("\\", "/").lower()
        now = time.time()

        if self.is_excluded(path) or self.is_excluded_file(path):
            return

        if path in self.recent_events and now - self.recent_events[path] < 5:
            return

        print(f"[DEBUG] File event: {path}")
        threading.Thread(target=self.wait_and_scan_file, args=(path,), daemon=True).start()



    def wait_and_scan_file(self, path):
        max_wait = 20
        waited = 0
        stable_counter = 0

        try:
            while waited < max_wait:
                if is_file_ready(path):
                    stable_counter += 1
                    if stable_counter >= 3:
                        break
                else:
                    stable_counter = 0
                time.sleep(0.5)
                waited += 0.5

            if stable_counter < 3:
                print(f"[WARNING] File never stabilized: {path}")
                return

            # Optional slight delay to avoid race with AV/browser
            time.sleep(0.2)

            if getattr(self.gui, "monitoring_active", False):
                print(f"[DEBUG] Scanning file: {path}")
                try:
                    matched, rule, file_path, meta_path = scan_file_for_realtime(path)

                    if matched and meta_path:
                        monitor_page = self.gui.pages.get("monitor")
                        if monitor_page and hasattr(monitor_page, "add_to_quarantine_listbox"):
                            monitor_page.add_to_quarantine_listbox(file_path, meta_path, [rule])

                        if hasattr(self.gui, "notify_threat_detected"):
                            self.gui.notify_threat_detected(file_path, [rule])
                except Exception as e:
                    print(f"[ERROR] Failed scanning {path}: {e}")
            else:
                self.pending_scan_files.add(path)
                print(f"[INFO] Queued for future scan: {path}")

        finally:
            self.recent_events[path] = time.time()
            self.already_scanned.discard(path)



    def process_pending_files(self):
        print("[INFO] Processing pending files...")
        for path in list(self.pending_scan_files):
            if os.path.exists(path):
                print(f"[INFO] Scanning pending: {path}")
                self.wait_and_scan_file(path)
        self.pending_scan_files.clear()
