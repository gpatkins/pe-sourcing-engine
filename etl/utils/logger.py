import logging
import sys
from pathlib import Path

# Define the log file path relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

def setup_logger(name: str):
    # Ensure log directory exists
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent adding duplicate handlers if re-imported
    if logger.handlers:
        return logger

    # 1. File Handler (So the Dashboard can see it)
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_fmt = logging.Formatter('%(asctime)s [%(name)s] %(message)s', datefmt='%H:%M:%S')
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    # 2. Console Handler (So you can still see it in CLI)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(file_fmt)
    logger.addHandler(console_handler)

    return logger
