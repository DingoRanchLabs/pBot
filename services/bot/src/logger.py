"""
Logging to both stdout and file.
"""

import logging
import os

# Params -----------------------------------------------------------------------

name              = "pbot-bot"
filename          = "pbot-bot.log"
file_log_level    = logging.NOTSET
console_log_level = file_log_level
file_format       = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
console_format    = '%(name)s - %(levelname)s - %(message)s'

# --------------------------------------------------------------------- / Params

path = os.path.join("./", filename)
logger = logging.getLogger(name)
logging.root.setLevel(logging.NOTSET)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(path)

c_handler.setLevel(logging.NOTSET)
f_handler.setLevel(logging.NOTSET)

c_format = logging.Formatter(console_format)
f_format = logging.Formatter(file_format)

c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)
