"""
MCP Tool Definitions for LeanMCP

Exports tool definitions for registration with the LeanMCP registry.
"""

from app.models.mcp import SATOR_MCP_TOOLS, get_tools_as_json


def get_mcp_tools() -> list[dict]:
    """Get all SATOR MCP tools as JSON-serializable dicts"""
    return get_tools_as_json()


def register_tools(registry_url: str | None = None) -> dict:
    """
    Register tools with a LeanMCP registry.
    
    Args:
        registry_url: URL of the LeanMCP registry (optional)
        
    Returns:
        Registration result
    """
    tools = get_mcp_tools()
    
    if registry_url is None:
        # Just return the tools that would be registered
        return {
            "status": "dry_run",
            "tools_count": len(tools),
            "tools": [t["name"] for t in tools],
        }
    
    # In a real implementation, this would POST to the registry
    # For now, we just simulate the registration
    return {
        "status": "registered",
        "registry": registry_url,
        "tools_count": len(tools),
        "tools": [t["name"] for t in tools],
    }


def get_tool_schema(tool_name: str) -> dict | None:
    """Get the JSON schema for a specific tool"""
    for tool in SATOR_MCP_TOOLS:
        if tool.name == tool_name:
            return tool.input_schema
    return None
