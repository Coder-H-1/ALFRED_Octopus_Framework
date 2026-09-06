"""
FmWk/tools/device_tools.py — Hardware, Battery, and Display Controls
"""

from typing import Dict, Any
import psutil
import screen_brightness_control as sbc
from ..core.decorators import mcp_tool


@mcp_tool(
    name="get_battery_status",
    description="Check system battery level and charging status.",
    category="device"
)
def get_battery_status() -> Dict[str, Any]:
    """Retrieves current battery percentage and AC connection state."""
    battery = psutil.sensors_battery()
    if not battery:
        return {"status": "No battery detected (Desktop or AC power only)."}

    percent = round(battery.percent)
    plugged = battery.power_plugged
    charging_text = "plugged in and charging" if plugged else "running on battery power"
    return {
        "status": f"Battery is at {percent}%, {charging_text}.",
        "percent": percent,
        "power_plugged": plugged
    }


@mcp_tool(
    name="set_screen_brightness",
    description="Set display brightness from 0 to 100 percent.",
    category="device"
)
def set_screen_brightness(level: int) -> Dict[str, Any]:
    """Adjusts primary display brightness level."""
    target = max(0, min(100, int(level)))
    try:
        sbc.set_brightness(target)
        return {"status": f"Display brightness set to {target}%, sir.", "brightness": target}
    except Exception as e:
        return {"error": f"Failed to set brightness: {e}"}


@mcp_tool(
    name="adjust_screen_brightness",
    description="Adjust screen brightness up or down relatively. Direction can be 'increase' or 'decrease'.",
    category="device"
)
def adjust_screen_brightness(direction: str = "increase", amount: int = 10) -> Dict[str, Any]:
    """Adjusts primary display brightness relatively."""
    try:
        current = sbc.get_brightness()
        cur_val = current[0] if isinstance(current, list) else current
        delta = amount if direction.lower() in ["increase", "up", "raise", "higher", "brighter"] else -amount
        new_val = max(0, min(100, int(cur_val + delta)))
        sbc.set_brightness(new_val)
        return {"status": f"Brightness adjusted to {new_val}%, sir.", "brightness": new_val}
    except Exception as e:
        return {"error": f"Failed to adjust brightness: {e}"}


@mcp_tool(
    name="get_screen_brightness",
    description="Get current display brightness percentage.",
    category="device"
)
def get_screen_brightness() -> Dict[str, Any]:
    """Returns current monitor brightness."""
    try:
        current = sbc.get_brightness()
        val = current[0] if isinstance(current, list) else current
        return {"status": f"Current screen brightness is {val}%, sir.", "brightness": val}
    except Exception as e:
        return {"error": f"Failed to read brightness: {e}"}
