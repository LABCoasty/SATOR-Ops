"""
LeanMCP Integration (Primary Sponsor)

Transport and registry layer for SATOR agent tools via MCP protocol.
"""

from .tools import get_mcp_tools, register_tools
from .server import MCPServer

__all__ = [
    "get_mcp_tools",
    "register_tools",
    "MCPServer",
]
