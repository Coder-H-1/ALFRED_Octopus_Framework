"""
FmWk/tools/web_tools.py — Fast Native Web Search and Information Extraction Tools
"""

import urllib.parse
import urllib.request
import json
from typing import Dict, Any, List
from ..core.decorators import mcp_tool


@mcp_tool(
    name="web_search",
    description="Quickly search the web for brief summaries, facts, or answers using DuckDuckGo.",
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
            return {"query": query, "status": abstract, "answer": abstract}

        topics = [
            t.get("Text") for t in data.get("RelatedTopics", [])
            if isinstance(t, dict) and "Text" in t
        ][:max_results]

        if topics:
            return {"query": query, "status": topics[0], "results": topics}
        return {"query": query, "status": f"No direct instant answer found for '{query}', sir."}
    except Exception as e:
        return {"query": query, "error": f"Search failed: {e}"}


@mcp_tool(
    name="web_search_extract",
    description="Extract detailed comprehensive information, Wikipedia extracts, and related links for a query.",
    category="web"
)
def web_search_extract(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Comprehensive extraction using Wikipedia API with DuckDuckGo fallback."""
    data = {
        "query": query,
        "details": [],
        "links": [],
        "images": []
    }

    # 1. Wikipedia API
    try:
        wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
        req = urllib.request.Request(wiki_search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as res:
            search_data = json.loads(res.read().decode('utf-8'))

        if search_data.get('query', {}).get('search'):
            title = search_data['query']['search'][0]['title']
            detail_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts|pageimages"
                f"&exintro&explaintext&titles={urllib.parse.quote(title)}&format=json&pithumbsize=500"
            )
            req2 = urllib.request.Request(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2, timeout=5) as detail_res:
                detail_json = json.loads(detail_res.read().decode('utf-8'))

            pages = detail_json.get('query', {}).get('pages', {})
            for page_id, page_info in pages.items():
                if 'extract' in page_info and page_info['extract']:
                    data['details'].append(page_info['extract'])
                if 'thumbnail' in page_info:
                    data['images'].append(page_info['thumbnail']['source'])

                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                data['links'].append({"title": f"{title} - Wikipedia", "url": page_url})

    except Exception:
        pass

    # 2. DuckDuckGo Fallback if Wikipedia had no details
    if not data['details']:
        try:
            from bs4 import BeautifulSoup
            import requests
            ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(ddg_url, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                snippets = []
                for snip in soup.find_all('a', class_='result__snippet', limit=max_results):
                    text = snip.get_text().strip()
                    if text:
                        snippets.append(text)
                if snippets:
                    data['details'].extend(snippets)
        except Exception:
            pass

    if data['details']:
        summary = data['details'][0]
        return {
            "status": summary,
            "details": data['details'],
            "links": data['links'],
            "images": data['images']
        }

    return {"error": f"Could not find information for '{query}', sir."}
