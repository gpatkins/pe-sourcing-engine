import os
from pathlib import Path

# Paths relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOCK_FILE = LOGS_DIR / "pipeline.lock"
STOP_FILE = LOGS_DIR / "stop.signal"

def set_running(job_name: str):
    """Creates a lock file to indicate a job is running."""
    # Ensure logs dir exists
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Clear any old stop signals first
    if STOP_FILE.exists():
        STOP_FILE.unlink()
        
    with open(LOCK_FILE, "w") as f:
        f.write(job_name)

def clear_running():
    """Removes the lock file."""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
    if STOP_FILE.exists():
        STOP_FILE.unlink()

def request_stop():
    """Creates a signal file telling scripts to abort."""
    # Only request stop if something is actually running
    if LOCK_FILE.exists():
        with open(STOP_FILE, "w") as f:
            f.write("STOP")

def should_stop() -> bool:
    """Check this inside loops to see if user clicked stop."""
    return STOP_FILE.exists()

def get_current_state() -> str:
    """Returns 'idle' or the name of the running job."""
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, "r") as f:
                return f.read().strip()
        except:
            return "Unknown Process"
    return "idle"
