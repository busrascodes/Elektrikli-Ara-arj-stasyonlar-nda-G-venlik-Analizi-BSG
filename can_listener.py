import os
import time
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "can_logs.txt")

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def follow_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Dosya yoksa oluştur
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"[{ts()}] [CAN Listener] (Windows) Log file created: {path}\n")

    print(f"[{ts()}] [CAN Listener] (Windows) Listening via log file: {path}")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        # dosyanın sonuna git (tail gibi)
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                print(line.rstrip("\n"))
            else:
                time.sleep(0.25)

if __name__ == "__main__":
    follow_file(LOG_FILE)
