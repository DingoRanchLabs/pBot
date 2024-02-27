"""
Logging to both stdout and file.
"""

import logging
import os

# Params -----------------------------------------------------------------------

NAME              = "pbot-listener"
FILENAME          = "pbot-listener.log"
FILE_LOG_LEVEL    = logging.NOTSET
CONSOLE_LOG_LEVEL = FILE_LOG_LEVEL
FILE_FORMAT       = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
CONSOLE_FORMAT    = '%(name)s - %(levelname)s - %(message)s'

# --------------------------------------------------------------------- / Params

path = os.path.join("./", FILENAME)
logger = logging.getLogger(NAME)
logging.root.setLevel(logging.NOTSET)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(path)

c_handler.setLevel(logging.NOTSET)
f_handler.setLevel(logging.NOTSET)

c_format = logging.Formatter(CONSOLE_FORMAT)
f_format = logging.Formatter(FILE_FORMAT)

c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)
