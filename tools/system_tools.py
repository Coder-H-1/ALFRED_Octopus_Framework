"""
FmWk/tools/system_tools.py — Native In-Process System Management Tools
"""

import subprocess
from typing import Dict, Any, Optional
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ..core.decorators import mcp_tool

APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "browser": "start chrome",
    "incognito chrome": "start chrome --incognito",
    "chrome": "start chrome",
    "terminal": "start powershell",
    "google": "start chrome google.com",
    "youtube": "start chrome https://youtube.com",
    "github": "start chrome https://github.com",
    "gemini": "start chrome https://gemini.google.com",
    "chatgpt": "start chrome https://chatgpt.com",
    "amazon": "start chrome https://amazon.in",
    "flipkart": "start chrome https://flipkart.com",
    "instagram": "start chrome https://instagram.com",
    "whatsapp": "start chrome https://web.whatsapp.com",
    "facebook": "start chrome https://facebook.com",
    "twitter": "start chrome https://twitter.com",
    "linkedin": "start chrome https://linkedin.com"
}

_volume_interface = None

def _get_volume_interface():
    global _volume_interface
    if not _volume_interface:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        _volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
    return _volume_interface


@mcp_tool(
    name="system_set_volume",
    description="Set system audio volume level to an exact percentage from 0 to 100.",
    category="system"
)
def set_volume(level: int) -> Dict[str, Any]:
    """Sets master volume on Windows host."""
    level = max(0, min(100, int(level)))
    try:
        vol = _get_volume_interface()
        vol.SetMasterVolumeLevelScalar(level / 100.0, None)
        return {"level": level, "status": f"Volume set to {level}%, sir."}
    except Exception as e:
        return {"error": f"Failed to set volume: {e}"}


@mcp_tool(
    name="system_adjust_volume",
    description="Adjust system audio volume up or down relatively. Direction can be 'increase' or 'decrease'.",
    category="system"
)
def adjust_volume(direction: str = "increase", amount: int = 10) -> Dict[str, Any]:
    """Increases or decreases master volume."""
    try:
        vol = _get_volume_interface()
        current = vol.GetMasterVolumeLevelScalar() * 100
        delta = amount if direction.lower() in ["increase", "up", "raise", "higher"] else -amount
        target = max(0, min(100, int(round(current + delta))))
        vol.SetMasterVolumeLevelScalar(target / 100.0, None)
        return {"level": target, "status": f"Volume set to {target}%, sir."}
    except Exception as e:
        return {"error": f"Failed to adjust volume: {e}"}


@mcp_tool(
    name="system_mute_volume",
    description="Toggle or enable mute on system audio volume.",
    category="system"
)
def mute_volume(mute_state: Optional[bool] = None) -> Dict[str, Any]:
    """Mutes or unmutes master audio."""
    try:
        vol = _get_volume_interface()
        if mute_state is None:
            current_mute = vol.GetMute()
            new_mute = 0 if current_mute else 1
        else:
            new_mute = 1 if mute_state else 0
        vol.SetMute(new_mute, None)
        msg = "Audio muted, sir." if new_mute else "Audio unmuted, sir."
        return {"muted": bool(new_mute), "status": msg}
    except Exception as e:
        return {"error": f"Failed to toggle mute: {e}"}


@mcp_tool(
    name="app_open",
    description="Launch desktop applications or websites on the host computer.",
    category="system"
)
def open_app(app_name: str) -> Dict[str, Any]:
    """Launches application executable."""
    clean_name = app_name.lower().strip()
    cmd = APP_MAP.get(clean_name, f"start {clean_name}")
    try:
        subprocess.Popen(cmd, shell=True)
        return {"status": f"Launched {app_name}, sir."}
    except Exception as e:
        return {"error": f"Failed to launch {app_name}: {e}"}
