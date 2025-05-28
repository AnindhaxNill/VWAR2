# Scanning/scanner_core.py

import traceback
from Scanning.yara_engine import compile_yara_rules
from Scanning.quarantine import quarantine_file
from utils.logger import log_message
import yara
# Compile rules once at module load
rules = compile_yara_rules()


def scan_file_for_realtime(file_path):
    """
    Scan a file with precompiled YARA rules and quarantine it if malicious.
    
    Returns:
        (matched: bool, rule: str | None, quarantined_path: str | None, meta_path: str | None)
    """
    if not rules:
        log_message("[ERROR] No YARA rules loaded.")
        return False, None, file_path, None

    try:
        # Match rules
        try:
            matches = rules.match(file_path, timeout=60)
        except yara.Error as e:
            log_message(f"[WARNING] YARA scan failed: {e} — file likely gone: {file_path}")
            return False, None, None, None


        if matches:
            rule = matches[0].rule
            # Quarantine the file and get the quarantine path
            # quarantine_path = quarantine_file(file_path, matched_rules=[rule])
            # meta_path = quarantine_path + ".meta"

            # log_message(f"[MATCH] {file_path} => Rule: {rule}")
            # return True, rule, quarantine_path, meta_path
            try:
                quarantine_path = quarantine_file(file_path, matched_rules=[rule])
            except RuntimeError as qe:
                # log_message(f"[WARNING] Could not quarantine (file may be gone): {qe}")
                print(f"[WARNING] Could not quarantine (file may be gone): {qe}")
                return False, None, file_path, None

            meta_path = quarantine_path + ".meta"
            log_message(f"[MATCH] {file_path} => Rule: {rule}")
            return True, rule, quarantine_path, meta_path

    except Exception:
        # Always return 4 items, never break unpacking
        log_message(f"[ERROR] Failed to scan {file_path}:\n{traceback.format_exc()}")

    return False, None, file_path, None
