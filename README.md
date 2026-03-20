# DennisLogseq MCP Server

A simple [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that connects Claude to your local [Logseq](https://logseq.com/) graph. Search pages and journal entries directly from Claude Desktop.

## Features

- **Full-text search** across all pages and journal entries
- **Browse pages** with optional name filtering
- **Read page content** including nested block hierarchies
- Zero external dependencies — uses only Python's standard library + the `mcp` package

## Prerequisites

- Python 3.10+
- [Logseq](https://logseq.com/) desktop app with the HTTP API server enabled
- [Claude Desktop](https://claude.ai/download)

### Enable the Logseq HTTP API

1. Open Logseq → **Settings** → **Features**
2. Enable **HTTP APIs server**
3. Click the plug icon (🔌) in the toolbar → **Start server**
4. Generate an API token under **Authorization tokens** and note it down

The server runs on `http://localhost:12315` by default.

## Installation

### 1. Install the MCP package

```bash
pip3 install mcp
```

### 2. Clone or download this server

```bash
git clone https://github.com/DennisFaucher/simple-logseq-mcp.git
# or just download server.py
```

### 3. Configure your API token

Open `server.py` and set your Logseq API token:

```python
LOGSEQ_TOKEN = "your-token-here"
```

### 4. Register with Claude Desktop

Add the following to your `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "DennisLogseq": {
      "command": "python3",
      "args": ["/path/to/DennisLogseq/server.py"],
      "env": {}
    }
  }
}
```

### 5. Restart Claude Desktop

The **DennisLogseq** tools will appear automatically in Claude's tool list.

## Tools

### `search_logseq(query)`

Full-text search across all pages and journal entries.

**Example:**
> "Search my Logseq notes for Shane Zabel"

Returns matching page titles and content snippets, with page names resolved from Logseq's internal IDs. Indicates when more results are available beyond the initial batch.

---

### `list_pages(filter_text?)`

List all pages in your graph, optionally filtered by name.

**Examples:**
> "List all my Logseq pages"
> "Find Logseq pages with 'RTX' in the name"

---

### `get_page(page_name)`

Retrieve the full content of a page or journal entry, including nested blocks.

**Examples:**
> "Show me the Logseq page 'My Project Notes'"
> "Get my Logseq journal for 2026-03-19"

Journal entries use date strings as their page name (e.g. `2026-03-19`).


## Project Structure

```
DennisLogseq/
└── server.py      # MCP server — all tools defined here
```

## How It Works

The Logseq desktop app exposes a local HTTP API at `http://localhost:12315/api`. Each request is a `POST` with a JSON body specifying a method name and arguments — mirroring Logseq's JavaScript plugin API:

```json
{
  "method": "logseq.search",
  "args": ["my query"]
}
```

This server wraps those calls in FastMCP tools, making them available to Claude as first-class capabilities.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot reach Logseq API` | Make sure Logseq is running and the HTTP server is started (🔌 button) |
| `Logseq API error 401` | Check your `LOGSEQ_TOKEN` matches the token in Logseq's API settings |
| Tools not showing in Claude | Restart Claude Desktop after editing `claude_desktop_config.json` |
| Page names showing as numbers | This is handled automatically — the server resolves numeric DB IDs to page names |

## License

MIT
