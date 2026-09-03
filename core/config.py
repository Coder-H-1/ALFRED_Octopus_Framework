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

def _expand_values(val: Any) -> Any:
    """Recursively expands environment variables (%VAR%, $VAR) and ~ user directories."""
    if isinstance(val, str):
        return os.path.expanduser(os.path.expandvars(val))
    elif isinstance(val, list):
        return [_expand_values(v) for v in val]
    elif isinstance(val, dict):
        return {k: _expand_values(v) for k, v in val.items()}
    return val

def load_server_config() -> Dict[str, Any]:
    """Loads MCP server configurations and settings from mcp_servers.json with dynamic path expansion."""
    if not os.path.isfile(_CONFIG_FILE):
        return {"settings": DEFAULT_SETTINGS, "mcpServers": {}}
        
    try:
        import orjson
        with open(_CONFIG_FILE, "rb") as f:
            data = orjson.loads(f.read())
    except Exception:
        import json
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    return _expand_values(data)

def get_settings() -> Dict[str, Any]:
    """Returns active runtime settings."""
    cfg = load_server_config()
    settings = dict(DEFAULT_SETTINGS)
    settings.update(cfg.get("settings", {}))
    return settings

def get_tools_dir() -> str:
    """Returns the absolute path to the local tools directory."""
    return _TOOLS_DIR
