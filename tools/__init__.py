"""
FmWk/tools/__init__.py — Auto-loader for Native In-Process Tools
"""

import os
import importlib
import logging

logger = logging.getLogger(__name__)

# Automatically import all tool modules in this folder
_CURRENT_DIR = os.path.dirname(__file__)
for filename in os.listdir(_CURRENT_DIR):
    if filename.endswith(".py") and not filename.startswith("__"):
        module_name = filename[:-3]
        try:
            importlib.import_module(f".{module_name}", package=__name__)
        except Exception as e:
            logger.warning(f"Failed to auto-load tool module {module_name}: {e}")
