"""
FmWk/tools/window_tools.py — Native In-Process Window Management Tools
"""

from typing import Dict, Any, List
import pygetwindow as gw
import win32gui
import win32con
from ..core.decorators import mcp_tool


@mcp_tool(
    name="window_bring_to_front",
    description="Bring an open application window to the foreground by its title or partial title.",
    category="window"
)
def window_bring_to_front(window_name: str) -> Dict[str, Any]:
    """Brings matching window to front."""
    try:
        matches = gw.getWindowsWithTitle(window_name)
        if not matches:
            return {"error": f"No window found matching '{window_name}', sir."}
        win = matches[0]
        win.activate()
        return {"status": f"Brought {win.title} to the foreground, sir."}
    except Exception as e:
        return {"error": f"Failed to activate window '{window_name}': {e}"}


@mcp_tool(
    name="window_resize",
    description="Resize an open window to specified width and height in pixels.",
    category="window"
)
def window_resize(window_name: str, width: int, height: int) -> Dict[str, Any]:
    """Resizes matching window."""
    try:
        matches = gw.getWindowsWithTitle(window_name)
        if not matches:
            return {"error": f"No window found matching '{window_name}', sir."}
        win = matches[0]
        win.resizeTo(int(width), int(height))
        return {"status": f"Resized {win.title} to {width}x{height}, sir."}
    except Exception as e:
        return {"error": f"Failed to resize window '{window_name}': {e}"}


@mcp_tool(
    name="window_move",
    description="Move an open window to specified screen coordinates (x, y).",
    category="window"
)
def window_move(window_name: str, x: int, y: int) -> Dict[str, Any]:
    """Moves matching window."""
    try:
        matches = gw.getWindowsWithTitle(window_name)
        if not matches:
            return {"error": f"No window found matching '{window_name}', sir."}
        win = matches[0]
        win.moveTo(int(x), int(y))
        return {"status": f"Moved {win.title} to ({x}, {y}), sir."}
    except Exception as e:
        return {"error": f"Failed to move window '{window_name}': {e}"}


@mcp_tool(
    name="window_manage_state",
    description="Change window state: 'minimize', 'maximize', or 'restore'.",
    category="window"
)
def window_manage_state(window_name: str, action: str) -> Dict[str, Any]:
    """Minimizes, maximizes, or restores a window."""
    try:
        matches = gw.getWindowsWithTitle(window_name)
        if not matches:
            return {"error": f"No window found matching '{window_name}', sir."}
        win = matches[0]
        hwnd = win._hWnd
        action_clean = action.lower().strip()

        if "min" in action_clean:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return {"status": f"Minimized {win.title}, sir."}
        elif "max" in action_clean:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return {"status": f"Maximized {win.title}, sir."}
        elif "restore" in action_clean:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return {"status": f"Restored {win.title}, sir."}
        else:
            return {"error": f"Unknown window action '{action}'. Use minimize, maximize, or restore."}
    except Exception as e:
        return {"error": f"Failed to adjust window state: {e}"}


@mcp_tool(
    name="window_list_open",
    description="List active desktop window titles.",
    category="window"
)
def window_list_open() -> Dict[str, Any]:
    """Returns visible open window titles."""
    try:
        titles = [w.title for w in gw.getAllWindows() if w.title.strip()]
        return {"status": f"Found {len(titles)} open windows.", "windows": titles[:10]}
    except Exception as e:
        return {"error": f"Failed to enumerate windows: {e}"}
