# MCP Standard I/O Wrapper

## Overview

`mcp_stdio_client.py` converts AI Knowledge Hub's REST API into standard MCP stdio protocol,
so external MCP clients (Claude Desktop, Cursor, Cline) can connect directly.

## Usage

### 1. Requirements
Python 3.8+ (stdlib only, no extra packages).

### 2. Get API Key
Get your API key from the **MCP Service** page in the web UI.

### 3. Quick Test
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_stdio_client.py --url http://YOUR_SERVER_IP --key YOUR_KEY
```

### 4. Claude Desktop

Edit `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ai-knowledge-hub": {
      "command": "python",
      "args": [
        "/path/to/mcp_stdio_client.py",
        "--url", "http://YOUR_SERVER_IP",
        "--key", "YOUR_API_KEY"
      ]
    }
  }
}
```

### 5. Cursor

Settings → MCP → Add Server:
```
Name: ai-knowledge-hub
Type: command
Command: python /path/to/mcp_stdio_client.py --url http://YOUR_SERVER_IP --key YOUR_KEY
```

## Available Tools

| Tool | Description |
|------|-------------|
| search_knowledge | Search knowledge base |
| get_document | Get document details |
| create_document | Create a knowledge document |
| graph_search | Get knowledge graph data |
| statistics | Get knowledge statistics |
| graph_statistics | Get graph statistics |
