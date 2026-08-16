import logging
import os
from datetime import datetime

def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{today_str}.log")

    logger = logging.getLogger("YoutubeAutomation")
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

logger = setup_logger()
