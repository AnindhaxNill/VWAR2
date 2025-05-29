import os
from datetime import datetime

LOG_PATH = os.path.join("data", "vwar.log")


def log_message(message: str, to_file: bool = True):
    """Log message to console and optionally to a log file."""
    timestamped = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    # print(timestamped)

    if to_file:
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(timestamped + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to write to log file: {e}")
