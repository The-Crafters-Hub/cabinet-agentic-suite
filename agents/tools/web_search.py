"""
agents/tools/web_search.py
Search pre-approved woodworking websites ONLY.
Never queries the open internet — all sources are in trusted_sources.json.

Public function:
    search_trusted_sources(query: str, top_n: int = 3) -> list[dict]
"""

import json
import logging
import os
import re
import urllib.parse

import requests

logger = logging.getLogger(__name__)

_SOURCES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "trusted_sources.json")
_TIMEOUT = 8  # seconds per HTTP request


def _load_sources() -> list[dict]:
    with open(_SOURCES_PATH, encoding="utf-8") as f:
        return json.load(f)


def search_trusted_sources(query: str, top_n: int = 3) -> list[dict]:
    """
    Search ONLY pre-approved woodworking websites.
    Returns snippets from sites that have search URLs configured.

    Args:
        query: Search query string.
        top_n: Max number of results to return.

    Returns:
        List of dicts: {source_name, url, snippet, type}
    """
    sources = _load_sources()
    results = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; TheCabinetBot/1.0; "
            "+https://the-crafters-hub.com)"
        )
    }

    for source in sources:
        # Skip internal DB sources (handled separately by search.py)
        if source.get("type") == "internal_db":
            continue

        search_url_template = source.get("search_url")
        if not search_url_template:
            continue

        # Build search URL
        encoded_query = urllib.parse.quote_plus(query)
        search_url = search_url_template.replace("{query}", encoded_query)

        try:
            response = requests.get(search_url, headers=headers, timeout=_TIMEOUT)
            if response.status_code != 200:
                continue

            # Extract readable text snippet from response (very lightweight)
            text = re.sub(r"<[^>]+>", " ", response.text)  # strip HTML tags
            text = re.sub(r"\s+", " ", text).strip()

            # Find a snippet around the query keywords
            q_words = query.lower().split()[:3]
            snippet = ""
            for word in q_words:
                idx = text.lower().find(word)
                if idx != -1:
                    start = max(0, idx - 100)
                    end   = min(len(text), idx + 300)
                    snippet = text[start:end].strip()
                    break

            if not snippet:
                snippet = text[:300]

            results.append({
                "source_name": source["name"],
                "url":         search_url,
                "snippet":     snippet,
                "type":        source.get("type", "website"),
                "focus":       source.get("focus", ""),
            })

            logger.info(f"Web result from {source['name']}: {len(snippet)} chars")

        except requests.RequestException as e:
            logger.warning(f"Could not reach {source['name']}: {e}")
            continue

        if len(results) >= top_n:
            break

    logger.info(f"Trusted web search '{query}': {len(results)} results")
    return results
