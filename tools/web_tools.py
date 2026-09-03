"""
FmWk/tools/web_tools.py — Fast Native Web Search Tools
"""

import urllib.parse
import urllib.request
import json
from typing import Dict, Any
from ..core.decorators import mcp_tool

@mcp_tool(
    name="web_search",
    description="Search the web for news, information, or answers.",
    category="web"
)
def web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Instant search using DuckDuckGo API."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
    req = urllib.request.Request(url, headers={"User-Agent": "ALFRED-Octopus-MCP/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        abstract = data.get("AbstractText", "")
        if abstract:
            return {"query": query, "answer": abstract}

        topics = [
            t.get("Text") for t in data.get("RelatedTopics", [])
            if isinstance(t, dict) and "Text" in t
        ][:max_results]

        return {
            "query": query,
            "results": topics or ["No direct answer found on DuckDuckGo."]
        }
    except Exception as e:
        return {"query": query, "error": f"Search failed: {e}"}
