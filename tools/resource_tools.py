"""
FmWk/tools/resource_tools.py — Native In-Process Resource Monitoring Tools
"""

import os
from typing import Dict, Any
import psutil
from ..core.decorators import mcp_tool


@mcp_tool(
    name="get_system_resources",
    description="Get real-time system CPU percentage and RAM usage details.",
    category="system"
)
def get_system_resources() -> Dict[str, Any]:
    """Returns CPU % and RAM details."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        virtual_mem = psutil.virtual_memory()

        ram_total_gb = round(virtual_mem.total / (1024 ** 3), 2)
        ram_used_gb = round(virtual_mem.used / (1024 ** 3), 2)
        ram_percent = virtual_mem.percent

        return {
            "status": (
                f"Sir, system CPU usage is currently at {cpu_percent} percent, "
                f"and RAM usage is at {ram_percent} percent, with {ram_used_gb} GB used out of {ram_total_gb} GB."
            ),
            "cpu_percent": cpu_percent,
            "ram_total_gb": ram_total_gb,
            "ram_used_gb": ram_used_gb,
            "ram_percent": ram_percent
        }
    except Exception as e:
        return {"error": f"Failed to retrieve system stats: {e}"}


@mcp_tool(
    name="get_process_resources",
    description="Get CPU and memory consumption of the ALFRED application process.",
    category="system"
)
def get_process_resources() -> Dict[str, Any]:
    """Returns resource stats for the ALFRED process."""
    try:
        process = psutil.Process(os.getpid())
        process_cpu = process.cpu_percent(interval=0.1)
        process_mem = process.memory_info().rss / (1024 ** 2)

        return {
            "status": f"ALFRED is consuming {round(process_mem, 2)} megabytes of memory and {process_cpu} percent CPU.",
            "process_cpu": process_cpu,
            "process_mem_mb": round(process_mem, 2)
        }
    except Exception as e:
        return {"error": f"Failed to retrieve process stats: {e}"}


@mcp_tool(
    name="get_resource_summary",
    description="Get a comprehensive voice-friendly status summary of system and assistant resources.",
    category="system"
)
def get_resource_summary() -> Dict[str, Any]:
    """Returns combined system and assistant resource overview."""
    sys_res = get_system_resources()
    proc_res = get_process_resources()

    if "error" in sys_res:
        return sys_res

    phrase = (
        f"Sir, system CPU usage is at {sys_res['cpu_percent']} percent, "
        f"RAM is at {sys_res['ram_percent']} percent ({sys_res['ram_used_gb']} GB used of {sys_res['ram_total_gb']} GB). "
        f"I am using {proc_res.get('process_mem_mb', 0)} megabytes of memory."
    )
    return {
        "status": phrase,
        "system": sys_res,
        "process": proc_res
    }
