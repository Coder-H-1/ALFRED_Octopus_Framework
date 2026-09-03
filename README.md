# FmWk: Octopus MCP (Model Context Protocol)

Octopus MCP is the pluggable tool execution engine for **ALFRED**, implementing Anthropic's Model Context Protocol (MCP) standard.

---

## Architecture Overview

1. **Intermediary Bridge (`FmWk/bridge.py`)**:
   - Manages an isolated `asyncio` event loop in a daemon thread.
   - Provides a strictly synchronous API for ALFRED (`bridge.route_and_execute(query)` / `bridge.call_tool(name, args)`).
   - Keeps ALFRED synchronous, fast, and free of async loop complications.

2. **Dual-Mode Routing (Strategy B)**:
   - **Step 1 (Fast-Path)**: Sub-1ms regex & keyword router checks obvious tool intents (`volume`, `search`, `open app`).
   - **Step 2 (Quantized Classifier)**: Optional Qwen 4-bit / TurboQuant classifier (~200MB RAM, <30ms latency) for speech argument parsing.
   - **Step 3 (Graceful Fallback)**: If no tool matches or if a tool fails, returns `{"handled": False}`, cascading query to ALFRED's main LLM.

3. **Subprocess Pooling & Active Memory Management**:
   - External GitHub MCP servers run over **stdio** (Node.js / Python).
   - Injected Node memory cap: `--max-old-space-size=64`.
   - **60-Second Idle Retirement**: Automatically terminates idle child processes and invokes `gc.collect()` to return ~200MB RAM to the OS.
   - **orjson Serialization**: Lightning-fast JSON-RPC 2.0 communication.

---

## Directory Structure

```
FmWk/
├── bridge.py              # Intermediary Sync-Async Bridge for ALFRED
├── mcp_servers.json       # Config registry for external GitHub stdio servers
├── core/
│   ├── client.py          # Fast orjson Stdio MCP Client with memory caps & idle timer
│   ├── config.py          # Configuration and path management
│   ├── decorators.py      # @mcp_tool decorator for native in-process tools
│   ├── keyword_router.py  # Strategy B regex fast-path matcher
│   └── qwen_classifier.py # Qwen 4-bit quantized classifier interface
├── tools/                 # Native in-process Python tools (<0.5ms)
│   ├── system_tools.py    # Volume and application launcher
│   └── web_tools.py       # DuckDuckGo search tool
└── README.md
```

---

## Adding External MCP Tools from GitHub

Open `FmWk/mcp_servers.json` and add your tool definition under `mcpServers`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\VIBHA\\Desktop"],
      "enabled": true
    }
  }
}
```

The bridge automatically discovers schemas, enforces memory limits, runs the tool on demand, and retires the process after 60 seconds of inactivity.
