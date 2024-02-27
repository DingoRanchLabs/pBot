"""
Test runner.
"""

import os, pathlib
import pytest

os.chdir(os.path.join(pathlib.Path.cwd(), "bot","tests"))
pytest.main(["-s"])
