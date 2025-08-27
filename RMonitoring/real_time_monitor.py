

#V111111111111111111111111111111111111111111111111
# import os
# import time
# import threading
# import getpass
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# from Scanning.scanner_core import scan_file_for_realtime
# from utils.logger import log_message
# from queue import Queue
# from pathlib import Path
# import string
# import subprocess
# from RMonitoring.pipe_client import start_pipe_reader, stop_pipe_reader


# def is_file_ready(path):
#     try:
#         if not os.path.exists(path):
#             return False
#         if os.path.getsize(path) == 0:
#             return False
#         with open(path, "rb") as f:
#             chunk = f.read(4096)
#             return bool(chunk)
#     except:
#         return False


# class RealTimeMonitor(FileSystemEventHandler):
#     def __init__(self, gui, watch_paths=None):
#         self.gui = gui

#         # Setup included folders if not passed
#         if watch_paths is None:
#             user_profile = Path(os.path.expanduser("~"))
#             self.included_folders = [
#                 str(user_profile / "Downloads"),
#                 str(user_profile / "Desktop"),
#                 str(user_profile / "Documents")
#             ]
#             # Add all non-C drives
#             for letter in string.ascii_uppercase:
#                 if letter == "C":
#                     continue
#                 drive_path = f"{letter}:/"
#                 if os.path.exists(drive_path):
#                     self.included_folders.append(drive_path)

#             valid_included_folders = [p for p in self.included_folders if os.path.exists(p)]
#             self.watch_paths = valid_included_folders
#         else:
#             self.watch_paths = watch_paths if isinstance(watch_paths, list) else [watch_paths]

#         print(f"[DEBUG] Included folders to watch: {self.watch_paths}")

#         self.observer = Observer()
#         self.recent_events = {}  # path -> timestamp
#         self.pending_scan_files = set()
#         self.already_scanned = set()

#         base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#         print(f"[DEBUG] Base directory (excluded): {base_dir}")

#         self.excluded_folders = [base_dir]
#         # Exclude recycle bins on all drives
#         for drive_letter in string.ascii_uppercase:
#             drive = f"{drive_letter}:\\"
#             recycle_bin = os.path.join(drive, "$Recycle.Bin")
#             if os.path.exists(drive):
#                 self.excluded_folders.append(recycle_bin)

#         self.excluded_extensions = (".tmp", ".log", ".lock", ".crdownload", ".part", ".ds_store", "thumbs.db")
#         self.excluded_prefixes = ("~$",)

#         self.scan_queue = Queue()
#         self.scan_worker = threading.Thread(target=self._scan_worker_loop, daemon=True)
#         self.scan_worker.start()

#         # C++ monitor related
#         self._cpp_proc = None
#         self._pipe_thread = None


#     # --- Watchdog monitoring methods (your existing system) ---

#     def start_watchdog(self):
#         print("[DEBUG] Starting watchdog observer")
#         for path in self.watch_paths:
#             print(f"  ➤ Watching: {path}")
#             try:
#                 self.observer.schedule(self, path=path, recursive=True)
#             except Exception as e:
#                 print(f"[ERROR] Failed to watch {path}: {e}")
#         self.observer.start()

#     def stop_watchdog(self):
#         print("[INFO] Stopping watchdog observer.")
#         self.observer.stop()
#         self.observer.join()

#     def is_excluded(self, path):
#         path = os.path.abspath(path).lower()
#         for folder in self.excluded_folders:
#             folder = os.path.abspath(folder).lower()
#             if folder in path:
#                 return True
#         return False

#     def is_excluded_file(self, path):
#         filename = os.path.basename(path).lower()
#         if filename.endswith(self.excluded_extensions) or filename.startswith(self.excluded_prefixes):
#             return True
#         try:
#             if os.path.exists(path) and os.path.getsize(path) == 0:
#                 return True
#         except:
#             return True
#         return False

#     def on_created(self, event):
#         if not event.is_directory:
#             self._handle_event(event.src_path)

#     def on_modified(self, event):
#         if not event.is_directory:
#             self._handle_event(event.src_path)

#     def _handle_event(self, path):
#         path = os.path.abspath(path).replace("\\", "/").lower()
#         now = time.time()

#         if self.is_excluded(path) or self.is_excluded_file(path):
#             return

#         if path in self.recent_events and now - self.recent_events[path] < 5:
#             return

#         self.scan_queue.put(path)


#     def wait_and_scan_file(self, path):
#         max_wait = 5
#         waited = 0
#         stable_counter = 0
#         try:
#             while waited < max_wait:
#                 if is_file_ready(path):
#                     stable_counter += 1
#                     if stable_counter >= 3:
#                         break
#                 else:
#                     stable_counter = 0
#                 time.sleep(0.5)
#                 waited += 0.5

#             if stable_counter < 3:
#                 print(f"[WARNING] File never stabilized: {path}")
#                 return

#             time.sleep(0.2)  # slight delay

#             if getattr(self.gui, "monitoring_active", False):
#                 try:
#                     matched, rule, file_path, meta_path = scan_file_for_realtime(path)
#                     if matched and meta_path:
#                         monitor_page = self.gui
#                         if monitor_page and hasattr(monitor_page, "add_to_quarantine_listbox"):
#                             monitor_page.add_to_quarantine_listbox(file_path, meta_path, [rule])
#                         if hasattr(self.gui, "notify_threat_detected"):
#                             self.gui.notify_threat_detected(file_path, [rule])
#                 except Exception as e:
#                     print(f"[ERROR] Failed scanning {path}: {e}")
#             else:
#                 self.pending_scan_files.add(path)
#                 print(f"[INFO] Queued for future scan: {path}")
#         finally:
#             self.recent_events[path] = time.time()
#             self.already_scanned.discard(path)

#     def process_pending_files(self):
#         print("[INFO] Processing pending files...")
#         for path in list(self.pending_scan_files):
#             if os.path.exists(path):
#                 print(f"[INFO] Scanning pending: {path}")
#                 self.wait_and_scan_file(path)
#         self.pending_scan_files.clear()

#     def _scan_worker_loop(self):
#         while True:
#             try:
#                 path = self.scan_queue.get()
#                 threading.Thread(target=self.wait_and_scan_file, args=(path,), daemon=True).start()
#             except Exception as e:
#                 print(f"[ERROR] Worker failed: {e}")


#     # --- New methods for C++ real-time monitor integration ---

#     def start_cpp_monitor_engine(self, exe_path=None, excludes=None):
#         """
#         Start the C++ monitor executable and pipe reader.
#         exe_path: path to vwar_monitor.exe (default: project_root/vwar_monitor/vwar_monitor.exe)
#         excludes: optional list of paths to exclude (strings).
#         """
#         if getattr(self, "_cpp_proc", None):
#             print("[INFO] C++ monitor already running.")
#             return

#         if exe_path is None:
#             exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vwar_monitor', 'vwar_monitor.exe'))

#         if not os.path.exists(exe_path):
#             print(f"[ERROR] C++ monitor executable not found: {exe_path}")
#             return

#         cmd = [exe_path]
#         if excludes:
#             for e in excludes:
#                 cmd.append(str(e))

#         try:
#             self._cpp_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#             print(f"[INFO] Started C++ monitor (pid {self._cpp_proc.pid})")
#         except Exception as e:
#             print(f"[ERROR] Failed to start C++ monitor: {e}")
#             self._cpp_proc = None
#             return

#         self._pipe_thread = start_pipe_reader(self.scan_queue)

#     def stop_cpp_monitor_engine(self):
#         """
#         Stop the pipe reader and terminate the C++ process if running.
#         """
#         try:
#             stop_pipe_reader()
#         except Exception:
#             pass

#         if getattr(self, "_cpp_proc", None):
#             try:
#                 self._cpp_proc.terminate()
#                 self._cpp_proc.wait(timeout=3)
#             except Exception:
#                 try:
#                     self._cpp_proc.kill()
#                 except Exception:
#                     pass
#             print("[INFO] C++ monitor stopped.")
#             self._cpp_proc = None
#             self._pipe_thread = None
#V111111111111111111111111111111111111111111111111



import os
import time
import threading
import subprocess
from queue import Queue
from pathlib import Path
from Scanning.scanner_core import scan_file_for_realtime
from RMonitoring.pipe_client import start_pipe_reader, stop_pipe_reader

def is_file_ready(path):
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return False
        with open(path, "rb") as f:
            return bool(f.read(4096))
    except:
        return False

class RealTimeMonitor:
    def __init__(self, gui):
        self.gui = gui
        self.scan_queue = Queue()
        self.pending_scan_files = set()
        self.already_scanned = set()
        self._cpp_proc = None
        self._pipe_thread = None

        # Start the scan worker
        self.scan_worker = threading.Thread(target=self._scan_worker_loop, daemon=True)
        self.scan_worker.start()

    # ---------------- Scan Worker ----------------
    def _scan_worker_loop(self):
        while True:
            path = self.scan_queue.get()
            threading.Thread(target=self.wait_and_scan_file, args=(path,), daemon=True).start()

    def wait_and_scan_file(self, path):
        max_wait = 5
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

            time.sleep(0.2)  # slight delay

            if getattr(self.gui, "monitoring_active", False):
                try:
                    matched, rule, file_path, meta_path = scan_file_for_realtime(path)
                    if matched and meta_path:
                        if hasattr(self.gui, "add_to_quarantine_listbox"):
                            self.gui.add_to_quarantine_listbox(file_path, meta_path, [rule])
                        if hasattr(self.gui, "notify_threat_detected"):
                            self.gui.notify_threat_detected(file_path, [rule])
                except Exception as e:
                    print(f"[ERROR] Failed scanning {path}: {e}")
            else:
                self.pending_scan_files.add(path)
                print(f"[INFO] Queued for future scan: {path}")
        finally:
            self.already_scanned.discard(path)

    # ---------------- Pipe Integration ----------------
    def start_cpp_monitor_engine(self, exe_path=None, excludes=None):
        if self._cpp_proc:
            print("[INFO] C++ monitor already running.")
            return

        if exe_path is None:
            exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vwar_monitor', 'vwar_monitor.exe'))

        if not os.path.exists(exe_path):
            print(f"[ERROR] C++ monitor executable not found: {exe_path}")
            return

        cmd = [exe_path]
        if excludes:
            cmd += [str(e) for e in excludes]

        try:
            self._cpp_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"[INFO] Started C++ monitor (pid {self._cpp_proc.pid})")
        except Exception as e:
            print(f"[ERROR] Failed to start C++ monitor: {e}")
            self._cpp_proc = None
            return

        # Start pipe reader to push detected files into scan_queue
        self._pipe_thread = start_pipe_reader(self.scan_queue)

    def stop_cpp_monitor_engine(self):
        try:
            stop_pipe_reader()
        except Exception:
            pass

        if self._cpp_proc:
            try:
                self._cpp_proc.terminate()
                self._cpp_proc.wait(timeout=3)
            except Exception:
                try:
                    self._cpp_proc.kill()
                except Exception:
                    pass
            print("[INFO] C++ monitor stopped.")
            self._cpp_proc = None
            self._pipe_thread = None

    # ---------------- Pending Files ----------------
    def process_pending_files(self):
        for path in list(self.pending_scan_files):
            if os.path.exists(path):
                self.wait_and_scan_file(path)
        self.pending_scan_files.clear()
