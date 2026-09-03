"""
FmWk/core/config.py — Configuration and Path Settings for Octopus MCP
"""

import os
from typing import Dict, Any

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # FmWk/
_CONFIG_FILE = os.path.join(_BASE_DIR, "mcp_servers.json")
_TOOLS_DIR = os.path.join(_BASE_DIR, "tools")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "node_max_old_space_size_mb": 64,
    "idle_timeout_seconds": 60,
    "aggressive_gc": True,
    "serialization": "orjson"
}

def load_server_config() -> Dict[str, Any]:
    """Loads MCP server configurations and settings from mcp_servers.json."""
    if not os.path.isfile(_CONFIG_FILE):
        return {"settings": DEFAULT_SETTINGS, "mcpServers": {}}
        
    try:
        import orjson
        with open(_CONFIG_FILE, "rb") as f:
            return orjson.loads(f.read())
    except Exception:
        import json
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def get_settings() -> Dict[str, Any]:
    """Returns active runtime settings."""
    cfg = load_server_config()
    settings = dict(DEFAULT_SETTINGS)
    settings.update(cfg.get("settings", {}))
    return settings

def get_tools_dir() -> str:
    """Returns the absolute path to the local tools directory."""
    return _TOOLS_DIR
