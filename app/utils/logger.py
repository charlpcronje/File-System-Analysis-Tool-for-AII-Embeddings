import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LOG_LEVELS = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'PROD': 50}
LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'False') == 'True'
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'app.log')
CURRENT_LOG_LEVEL = LOG_LEVELS.get(os.getenv('LOG_LEVEL', 'DEBUG'), 10)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('app.log')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def log(message, condition=True, exit_after=False, level='INFO'):
    if LOG_LEVELS.get(level, 10) >= CURRENT_LOG_LEVEL and condition:
        final_message = f"{level}: {message}"
        if LOG_TO_FILE:
            with open(LOG_FILE_PATH, 'a') as file:
                file.write(final_message + "\n")
        else:
            print(final_message)

        if exit_after:
            exit(1)
"""
USAGE:
log("Reached a critical section in the code", level='DEBUG')
log("Variable A is greater than Variable B", A > B, level='INFO')
log("Unexpected value encountered", condition=False, exit_after=True, level='ERROR')
"""
