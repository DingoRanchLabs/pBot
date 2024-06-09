"""
Tranceiver-service logging to both stdout and file.
"""

import logging
import os
from dotenv import load_dotenv


load_dotenv()

# Params -----------------------------------------------------------------------

FILENAME          = "xceiver.log"
NAME              = os.path.basename(FILENAME)
FILE_LOG_LEVEL    = logging.NOTSET
CONSOLE_LOG_LEVEL = FILE_LOG_LEVEL
FILE_FORMAT       = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
CONSOLE_FORMAT    = '%(name)s - %(levelname)s - %(message)s'

# --------------------------------------------------------------------- / Params

logger = logging.getLogger(NAME)
logging.root.setLevel(logging.NOTSET)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(os.path.join("./", FILENAME))

c_handler.setLevel(CONSOLE_LOG_LEVEL)
f_handler.setLevel(FILE_LOG_LEVEL)

c_format = logging.Formatter(CONSOLE_FORMAT)
f_format = logging.Formatter(FILE_FORMAT)

c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)
