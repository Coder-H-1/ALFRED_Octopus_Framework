"""
FmWk/tools/system_tools.py — Native In-Process System Management Tools
"""

import subprocess
from typing import Dict, Any
from ..core.decorators import mcp_tool

APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "browser": "start chrome",
    "incognito chrome" : "start chrome --incognito",
    "chrome": "start chrome",
    "terminal": "start powershell",
    "google": "start chrome google.com",
    "youtube": "start chrome https://youtube.com",
    "github": "start chrome https://github.com",
    "gemini" : "start chrome https://gemini.google.com",
    "chatgpt" : "start chrome https://chatgpt.com",
    "amazon" : "start chrome https://amazon.in",
    "flipkart" : "start chrome https://flipkart.com",
    "instagram" : "start chrome https://instagram.com",
    "whatsapp" : "start chrome https://web.whatsapp.com",
    "facebook" : "start chrome https://facebook.com",
    "twitter" : "start chrome https://twitter.com",
    "linkedin" : "start chrome https://linkedin.com"
}

@mcp_tool(
    name="system_set_volume",
    description="Adjust system audio volume level from 0 to 100 percent.",
    category="system"
)
def set_volume(level: int) -> Dict[str, Any]:
    """Sets master volume on Windows host."""
    level = max(0, min(100, int(level)))
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return {"level": level, "status": f"Volume set to {level}%"}
    except Exception as e:
        return {"level": level, "warning": f"Pycaw adjustment failed ({e}), level saved."}


@mcp_tool(
    name="app_open",
    description="Launch desktop applications on the host computer.",
    category="system"
)
def open_app(app_name: str) -> Dict[str, Any]:
    """Launches application executable."""
    clean_name = app_name.lower().strip()
    cmd = APP_MAP.get(clean_name, f"start {clean_name}")
    try:
        subprocess.Popen(cmd, shell=True)
        return {"status": f"Launched {app_name}"}
    except Exception as e:
        return {"error": f"Failed to launch {app_name}: {e}"}
