import logging
import os

LOG_FILE = 'error.log'

_initialized = False

def init_logging():
    global _initialized
    if _initialized:
        return
    # Ensure directory if user wants later to change path
    log_path = os.path.join(os.getcwd(), LOG_FILE)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.getLogger(__name__).info('Logging initialized -> %s', log_path)
    _initialized = True

def get_logger(name: str):
    init_logging()
    return logging.getLogger(name)
