#!/usr/bin/env python3
"""
DennisLogseq MCP Server
Search Logseq pages and journals via the Logseq HTTP API.
"""

import json
import logging
import urllib.request
import urllib.error

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOGSEQ_API_URL = "http://localhost:12315/api"
LOGSEQ_TOKEN = "claude_desktop_is_groovy"

mcp = FastMCP("DennisLogseq")


def logseq_request(method: str, args: list) -> any:
    """Make a POST request to the Logseq HTTP API."""
    payload = json.dumps({"method": method, "args": args}).encode("utf-8")
    req = urllib.request.Request(
        LOGSEQ_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LOGSEQ_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body.strip() else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Logseq API error {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach Logseq API at {LOGSEQ_API_URL}: {e.reason}")


def flatten_blocks(blocks: list, depth: int = 0) -> str:
    """Recursively flatten a block tree into readable text."""
    lines = []
    for block in blocks or []:
        content = block.get("content", "").strip()
        if content:
            indent = "  " * depth
            lines.append(f"{indent}{content}")
        children = block.get("children", [])
        if children:
            lines.append(flatten_blocks(children, depth + 1))
    return "\n".join(lines)


def get_page_name_by_id(page_id: int) -> str:
    """Look up a page's display name by its numeric DB id."""
    try:
        page = logseq_request("logseq.Editor.getPage", [page_id])
        if page and isinstance(page, dict):
            return page.get("originalName") or page.get("name") or str(page_id)
    except Exception:
        pass
    return str(page_id)


def extract_block_page_name(block: dict) -> str:
    """Extract a readable page name from a search-result block."""
    # Try plain "page" key first
    page_val = block.get("page") or block.get("block/page")
    if page_val is None:
        return "Unknown page"
    if isinstance(page_val, str):
        return page_val
    if isinstance(page_val, int):
        return get_page_name_by_id(page_val)
    if isinstance(page_val, dict):
        # {"originalName": ...} or {"name": ...} or {"id": ...} or {"db/id": ...}
        name = page_val.get("originalName") or page_val.get("name")
        if name:
            return name
        pid = page_val.get("id") or page_val.get("db/id")
        if pid is not None:
            return get_page_name_by_id(int(pid))
    return "Unknown page"


def extract_block_content(block: dict) -> str:
    """Extract content text from a search-result block."""
    return (block.get("content") or block.get("block/content") or "").strip()


@mcp.tool()
def search_logseq(query: str) -> str:
    """
    Search across all Logseq pages and journal entries for the given query string.
    Returns matching page titles and block content snippets.

    Args:
        query: The text to search for across pages and journals.
    """
    logger.info(f"Searching Logseq for: {query}")
    results = logseq_request("logseq.search", [query])

    if not results:
        return f"No results found for '{query}'."

    output_parts = []
    has_more = results.get("has-more?") or results.get("hasMore") or False

    # Pages whose titles match the query
    pages = results.get("pages", [])
    if pages:
        output_parts.append(f"## Pages matching '{query}' ({len(pages)} found)\n")
        for page in pages:
            name = page if isinstance(page, str) else (page.get("originalName") or page.get("name", "Unknown"))
            output_parts.append(f"- {name}")

    # Block/content matches
    blocks = results.get("blocks", [])
    if blocks:
        output_parts.append(f"\n## Content matches ({len(blocks)} shown{'...' if has_more else ''})\n")
        for block in blocks:
            page_name = extract_block_page_name(block)
            content = extract_block_content(block)
            if content:
                output_parts.append(f"**[{page_name}]**\n{content[:400]}\n")

    if has_more:
        output_parts.append("\n*(More results exist — refine your query to narrow results.)*")

    return "\n".join(output_parts) if output_parts else f"No results found for '{query}'."


@mcp.tool()
def list_pages(filter_text: str = "") -> str:
    """
    List all pages in the Logseq graph.
    Optionally filter by text to find pages whose names contain the filter string.

    Args:
        filter_text: Optional text to filter page names (case-insensitive). Leave empty to list all pages.
    """
    logger.info("Listing Logseq pages")
    pages = logseq_request("logseq.Editor.getAllPages", [])

    if not pages:
        return "No pages found in Logseq graph."

    # Filter out journal pages and system pages unless specifically requested
    page_names = []
    for page in pages:
        name = page.get("originalName") or page.get("name", "")
        if not name:
            continue
        if filter_text and filter_text.lower() not in name.lower():
            continue
        page_names.append(name)

    page_names.sort()

    if not page_names:
        return f"No pages found matching '{filter_text}'."

    count = len(page_names)
    header = f"## Logseq Pages ({count} total)\n"
    return header + "\n".join(f"- {name}" for name in page_names)


@mcp.tool()
def get_page(page_name: str) -> str:
    """
    Get the full content of a specific Logseq page or journal entry by name.
    Returns the page's blocks as readable text.

    Args:
        page_name: The exact name of the page (e.g. 'My Project Notes' or '2024-01-15' for journals).
    """
    logger.info(f"Getting Logseq page: {page_name}")

    # Get page metadata
    page_info = logseq_request("logseq.Editor.getPage", [page_name])
    if not page_info:
        return f"Page '{page_name}' not found in Logseq."

    # Get page blocks
    blocks = logseq_request("logseq.Editor.getPageBlocksTree", [page_name])

    name = page_info.get("originalName") or page_info.get("name", page_name)
    journal = page_info.get("journal?") or page_info.get("journalDay")
    page_type = "Journal" if journal else "Page"

    output_parts = [f"## {page_type}: {name}\n"]

    if blocks:
        content = flatten_blocks(blocks)
        if content.strip():
            output_parts.append(content)
        else:
            output_parts.append("*(empty page)*")
    else:
        output_parts.append("*(no blocks found)*")

    return "\n".join(output_parts)


if __name__ == "__main__":
    mcp.run()
