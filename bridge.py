"""
FmWk/bridge.py — Intermediary Sync-to-Async Bridge between ALFRED and Octopus MCP

Features:
- Runs an isolated asyncio event loop in a background daemon thread.
- ALFRED uses purely synchronous calls: bridge.route_and_execute(query) or bridge.call_tool(name, args).
- Executes Strategy B:
    1. Keyword fast-path (sub-1ms regex check) -> calls matched MCP tool.
    2. Fallback to Qwen 4-bit tool classifier.
    3. If no tool matches or tool fails -> returns {"handled": False} so ALFRED cascades to its main LLM.
- Dispatches to:
    - In-process native tools (<0.5ms)
    - External stdio MCP servers (Node.js/Python with memory caps & 60s idle retirement)
"""

import os
import sys
import asyncio
import threading
import atexit
from concurrent.futures import Future
from typing import Dict, Any, List, Optional

from .core.config import load_server_config, get_settings
from .core.client import StdioMCPClient
from .core.decorators import LOCAL_TOOL_REGISTRY, get_local_tools, call_local_tool
from .core.keyword_router import KeywordRouter
from .core.qwen_classifier import QwenToolClassifier
import FmWk.tools  # Trigger auto-registration of local tools


class MCPBridge:
    """Intermediary bridge managing MCP tools and providing synchronous interface to ALFRED."""

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True, name="OctopusMCPBridge")
        self._thread.start()

        self._keyword_router = KeywordRouter()
        self._qwen_classifier = QwenToolClassifier()
        self._external_clients: Dict[str, StdioMCPClient] = {}
        self._tools_cache: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

        self._init_external_clients()
        self._build_tool_cache()
        atexit.register(self.shutdown)

    def _run_event_loop(self):
        """Runs the background asyncio event loop indefinitely."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _init_external_clients(self):
        """Initializes configured stdio MCP clients from mcp_servers.json."""
        config = load_server_config()
        servers = config.get("mcpServers", {})

        for name, srv in servers.items():
            if not srv.get("enabled", False):
                continue
            cmd = srv.get("command")
            args = srv.get("args", [])
            env = srv.get("env")
            if cmd:
                self._external_clients[name] = StdioMCPClient(
                    name=name,
                    command=cmd,
                    args=args,
                    env=env
                )

    def _build_tool_cache(self):
        """Caches schemas for all in-process tools and enabled external tools."""
        self._tools_cache.clear()

        # 1. Native in-process tools
        for tool in get_local_tools():
            self._tools_cache[tool["name"]] = {
                "source": "local",
                "schema": tool
            }

        # 2. External clients
        for client_name, client in self._external_clients.items():
            try:
                external_tools = client.list_tools()
                for t in external_tools:
                    tool_key = f"{client_name}__{t['name']}"
                    self._tools_cache[tool_key] = {
                        "source": "external",
                        "client": client,
                        "raw_name": t["name"],
                        "schema": t
                    }
            except Exception:
                pass

        self._initialized = True

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """Returns schemas of all available tools for LLM prompting."""
        return [entry["schema"] for entry in self._tools_cache.values()]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """
        Synchronous tool execution facade for ALFRED.
        Blocks until tool execution completes or times out.
        """
        if tool_name in LOCAL_TOOL_REGISTRY:
            return call_local_tool(tool_name, arguments)

        # Check external tool cache
        entry = self._tools_cache.get(tool_name)
        if entry and entry["source"] == "external":
            client: StdioMCPClient = entry["client"]
            raw_name = entry["raw_name"]
            return client.call_tool(raw_name, arguments, timeout=timeout)

        # Direct external fallback search
        for client in self._external_clients.values():
            tools = client.list_tools()
            if any(t.get("name") == tool_name for t in tools):
                return client.call_tool(tool_name, arguments, timeout=timeout)

        return {"success": False, "error": f"Tool '{tool_name}' not found."}

    def route_and_execute(self, query: str) -> Dict[str, Any]:
        """
        Strategy B Pipeline:
        1. Fast-path regex / keyword check (sub-1ms)
        2. If matched, call tool via bridge
        3. If no match or tool failure, cascade down to Qwen classifier / ALFRED LLM
        """
        clean_query = query.strip()
        if not clean_query:
            return {"handled": False, "reason": "empty_query"}

        # Step 1: Keyword / Fast-Path
        match_info = self._keyword_router.match(clean_query)
        if match_info and match_info.get("matched"):
            tool_name = match_info["tool_name"]
            arguments = match_info.get("arguments", {})

            result = self.call_tool(tool_name, arguments)
            if result.get("success"):
                return {
                    "handled": True,
                    "strategy": "keyword_fast_path",
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result.get("result", result)
                }
            # If tool call failed, don't crash ALFRED, cascade down
            return {
                "handled": False,
                "strategy": "keyword_fast_path_failed",
                "tool": tool_name,
                "error": result.get("error")
            }

        # Step 2: Qwen 4-bit Quantized Classifier (if active)
        if self._qwen_classifier.is_ready():
            qwen_res = self._qwen_classifier.classify(clean_query, self.get_all_tool_schemas())
            if qwen_res and "tool_name" in qwen_res:
                tool_name = qwen_res["tool_name"]
                args = qwen_res.get("arguments", {})
                res = self.call_tool(tool_name, args)
                if res.get("success"):
                    return {
                        "handled": True,
                        "strategy": "qwen_classifier",
                        "tool": tool_name,
                        "arguments": args,
                        "result": res.get("result", res)
                    }

        # Step 3: No tool handled this query; pass through to ALFRED LLM
        return {
            "handled": False,
            "reason": "no_tool_matched"
        }

    def shutdown(self):
        """Terminates all external subprocesses and stops the background loop."""
        for client in self._external_clients.values():
            try:
                client.terminate()
            except Exception:
                pass

        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)


# Global singleton instance
_GLOBAL_BRIDGE: Optional[MCPBridge] = None

def get_bridge() -> MCPBridge:
    """Retrieves or instantiates the global singleton MCP bridge."""
    global _GLOBAL_BRIDGE
    if _GLOBAL_BRIDGE is None:
        _GLOBAL_BRIDGE = MCPBridge()
    return _GLOBAL_BRIDGE
