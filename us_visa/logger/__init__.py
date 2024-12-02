import logging
import os
from datetime import datetime

try:
    # Ensure `from_root` is correctly imported and working
    from from_root import from_root
except ImportError:
    # Fallback for testing
    from_root = os.getcwd

LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
log_dir = 'logs'

# Define the full logs path
logs_path = os.path.join(from_root(), log_dir, LOG_FILE)

# Ensure directory exists
os.makedirs(os.path.dirname(logs_path), exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=logs_path,
    format="[ %(asctime)s ] %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

# Debug: Print the log file path
print(f"Log file created at: {logs_path}")

# # Test logs
# logging.info("Logging setup completed.")
# logging.debug("This is a debug message.")
# logging.error("This is an error message.")
