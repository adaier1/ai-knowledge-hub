#!/usr/bin/env python3
"""
AI Knowledge Hub - MCP Standard I/O Wrapper
============================================
Converts the REST API into standard MCP protocol (stdio transport),
so external MCP clients (Claude Desktop, Cursor, etc.) can connect.

Usage:
  python mcp_stdio_client.py --url http://YOUR_SERVER_IP --key YOUR_API_KEY

Or set environment variables:
  export AKH_URL=http://YOUR_SERVER_IP
  export AKH_KEY=your_api_key
  python mcp_stdio_client.py

Claude Desktop config (claude_desktop_config.json):
  {
    "mcpServers": {
      "ai-knowledge-hub": {
        "command": "python",
        "args": ["/path/to/mcp_stdio_client.py", "--url", "http://YOUR_SERVER_IP", "--key", "YOUR_KEY"],
        "env": {}
      }
    }
  }
"""

import sys
import json
import argparse
import urllib.request
import urllib.error
import urllib.parse

def parse_args():
    parser = argparse.ArgumentParser(description="AI Knowledge Hub MCP stdio wrapper")
    parser.add_argument("--url", default=None, help="Server URL (e.g. http://YOUR_SERVER_IP)")
    parser.add_argument("--key", default=None, help="API key")
    return parser.parse_args()

def get_config():
    args = parse_args()
    url = args.url
    key = args.key
    # Try environment variables
    import os
    if not url:
        url = os.environ.get("AKH_URL", "http://YOUR_SERVER_IP:8000")
    if not key:
        key = os.environ.get("AKH_KEY", "")
    # Remove trailing slash
    url = url.rstrip("/")
    # Default port 8000 if no port specified and not standard HTTP/HTTPS port
    parsed = urllib.parse.urlparse(url)
    if not parsed.port and parsed.scheme == "http":
        url = url + ":8000"
    return url, key


def http_get(url: str, key: str, path: str) -> dict:
    """Make a GET request to the server."""
    full_url = url + path
    if key:
        sep = "&" if "?" in path else "?"
        full_url = url + path + sep + "key=" + urllib.parse.quote(key)
    req = urllib.request.Request(full_url)
    if key and "?" not in path:
        req.add_header("Authorization", "Bearer " + key)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        raise Exception(f"Connection failed: {e.reason}")


def http_post(url: str, key: str, path: str, data: dict) -> dict:
    """Make a POST request to the server."""
    full_url = url + path
    if key:
        sep = "&" if "?" in path else "?"
        full_url = url + path + sep + "key=" + urllib.parse.quote(key)
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(full_url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if key and "?" not in path:
        req.add_header("Authorization", "Bearer " + key)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        raise Exception(f"Connection failed: {e.reason}")


def load_tools(url: str, key: str) -> list:
    """Fetch tool definitions from the MCP endpoint."""
    try:
        info = http_get(url, key, "/mcp")
        tools = info.get("tools", [])
        return tools
    except Exception as e:
        # Fallback: return hardcoded tool list
        return [
            {"name": "search_knowledge", "description": "Search knowledge base", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
            {"name": "get_document", "description": "Get document by ID", "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}},
            {"name": "create_document", "description": "Create a document", "input_schema": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "summary": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["title", "content"]}},
            {"name": "graph_search", "description": "Get knowledge graph data", "input_schema": {"type": "object", "properties": {"center_id": {"type": "integer"}, "depth": {"type": "integer", "default": 1}}}},
            {"name": "statistics", "description": "Get knowledge statistics", "input_schema": {"type": "object", "properties": {}}},
            {"name": "graph_statistics", "description": "Get graph statistics", "input_schema": {"type": "object", "properties": {}}},
        ]


def call_tool(url: str, key: str, tool_name: str, arguments: dict) -> dict:
    """Call a tool via the REST API."""
    try:
        result = http_post(url, key, f"/mcp/tools/{tool_name}", {
            "arguments": arguments
        })
        return result.get("result", result)
    except Exception as e:
        # Try alternative: direct API call
        try:
            if tool_name == "search_knowledge":
                q = arguments.get("query", "")
                limit = arguments.get("limit", 10)
                resp = http_post(url, key, "/api/search", {"query": q, "search_type": "hybrid", "limit": limit})
                return {"results": resp.get("results", [])}
            elif tool_name == "get_document":
                doc_id = arguments.get("id", 0)
                resp = http_get(url, key, f"/api/knowledge/{doc_id}")
                return {"document": resp}
            elif tool_name == "create_document":
                resp = http_post(url, key, "/api/knowledge", arguments)
                return {"id": resp.get("id"), "title": resp.get("title", ""), "message": "Created"}
            elif tool_name == "graph_search":
                params = {}
                if "center_id" in arguments:
                    params["center_id"] = arguments["center_id"]
                if "depth" in arguments:
                    params["depth"] = arguments["depth"]
                qs = "&".join(f"{k}={v}" for k, v in params.items())
                resp = http_get(url, key, f"/api/graph?{qs}")
                return resp
            elif tool_name == "statistics":
                return http_get(url, key, "/api/analytics/dashboard")
            elif tool_name == "graph_statistics":
                return http_get(url, key, "/api/graph/statistics")
            else:
                raise Exception(f"Unknown tool: {tool_name}")
        except Exception as e2:
            raise Exception(f"Tool call failed: {e2}")


def handle_message(url: str, key: str, tools_cache: list, msg: dict) -> dict | None:
    """Handle a single JSON-RPC message from stdin."""
    msg_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params", {})

    # Handle methods with no id (notifications)
    if msg_id is None:
        return None

    result = None
    error = None

    try:
        if method == "initialize":
            client_info = params.get("clientInfo", {})
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                        "supports": {
                            "list": True,
                            "call": True
                        }
                    }
                },
                "serverInfo": {
                    "name": "ai-knowledge-hub",
                    "version": "1.0.0"
                }
            }
        elif method == "tools/list":
            result = {"tools": tools_cache}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            call_result = call_tool(url, key, tool_name, arguments)
            # Format result for MCP
            content = []
            if isinstance(call_result, dict):
                content.append({
                    "type": "text",
                    "text": json.dumps(call_result, ensure_ascii=False, indent=2)
                })
            elif isinstance(call_result, list):
                content.append({
                    "type": "text",
                    "text": json.dumps(call_result, ensure_ascii=False, indent=2)
                })
            else:
                content.append({
                    "type": "text",
                    "text": str(call_result)
                })
            result = {"content": content}
        elif method == "notifications/initialized":
            return None
        elif method == "notifications/cancelled":
            return None
        else:
            error = {"code": -32601, "message": f"Method not found: {method}"}
    except Exception as e:
        error = {"code": -32603, "message": str(e)}

    response = {"jsonrpc": "2.0", "id": msg_id}
    if error:
        response["error"] = error
    else:
        response["result"] = result
    return response


def send_response(resp: dict):
    """Send a JSON-RPC response to stdout in MCP format."""
    text = json.dumps(resp, ensure_ascii=False)
    sys.stdout.write("Content-Length: " + str(len(text.encode("utf-8"))) + "\r\n\r\n")
    sys.stdout.write(text)
    sys.stdout.flush()


def read_message() -> dict | None:
    """Read a single JSON-RPC message from stdin (MCP stdio format)."""
    try:
        # Read headers
        headers = {}
        while True:
            line = sys.stdin.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if ": " in line:
                key, val = line.split(": ", 1)
                headers[key.lower()] = val

        content_length = int(headers.get("content-length", 0))
        if content_length == 0:
            return None

        body = sys.stdin.read(content_length)
        if not body:
            return None
        return json.loads(body)
    except (EOFError, json.JSONDecodeError, ValueError):
        return None


def main():
    url, key = get_config()
    
    # Print startup info to stderr (not stdout, which is for protocol)
    print(f"[MCP] Connecting to: {url}", file=sys.stderr)
    print(f"[MCP] Loading tools...", file=sys.stderr)
    
    # Load tools
    tools_cache = load_tools(url, key)
    print(f"[MCP] Loaded {len(tools_cache)} tools", file=sys.stderr)
    
    # Main loop: read messages from stdin, process, write to stdout
    while True:
        msg = read_message()
        if msg is None:
            break
        resp = handle_message(url, key, tools_cache, msg)
        if resp is not None:
            send_response(resp)
    
    print(f"[MCP] Connection closed", file=sys.stderr)


if __name__ == "__main__":
    main()
