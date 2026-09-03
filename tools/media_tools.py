"""
FmWk/tools/media_tools.py — Media Controls for YouTube, Spotify, and System Audio
"""

from typing import Dict, Any
import keyboard
from ..core.decorators import mcp_tool


@mcp_tool(
    name="media_play_pause",
    description="Toggle media playback (play or pause active audio/video).",
    category="media"
)
def media_play_pause() -> Dict[str, Any]:
    """Sends Windows global play/pause media key."""
    try:
        keyboard.send("play/pause media")
        return {"status": "Toggled media playback."}
    except Exception as e:
        return {"error": f"Failed to toggle media: {e}"}


@mcp_tool(
    name="media_next",
    description="Skip to the next media track or video.",
    category="media"
)
def media_next() -> Dict[str, Any]:
    """Sends Windows global next track key."""
    try:
        keyboard.send("next track")
        return {"status": "Skipped to next track."}
    except Exception as e:
        return {"error": f"Failed to skip track: {e}"}


@mcp_tool(
    name="media_previous",
    description="Go to previous media track or video.",
    category="media"
)
def media_previous() -> Dict[str, Any]:
    """Sends Windows global previous track key."""
    try:
        keyboard.send("previous track")
        return {"status": "Returned to previous track."}
    except Exception as e:
        return {"error": f"Failed to go back: {e}"}


@mcp_tool(
    name="media_stop",
    description="Stop active media playback.",
    category="media"
)
def media_stop() -> Dict[str, Any]:
    """Sends Windows global stop media key."""
    try:
        keyboard.send("stop media")
        return {"status": "Stopped media playback."}
    except Exception as e:
        return {"error": f"Failed to stop media: {e}"}
