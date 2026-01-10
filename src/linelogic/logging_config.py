"""
Logging configuration for LineLogic.

Provides a configured logger instance with telemetry support.
"""

import logging
import sys
from pathlib import Path

from linelogic.config.settings import settings

# Ensure log directory exists
log_dir = Path(".linelogic")
log_dir.mkdir(exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(".linelogic/linelogic.log"),
    ],
)

# Get logger for LineLogic
logger = logging.getLogger("linelogic")
