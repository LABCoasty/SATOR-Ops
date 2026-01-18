"""
LeanMCP Integration - MCP transport layer for SATOR decision tools.

Provides MCP-compliant tool server that exposes SATOR decision tools
for structured invocation by AI agents and backend services.
"""

from .server import MCPServer, MCPRequest, MCPResponse, get_mcp_server
from .tools import (
    SATOR_TOOLS,
    ToolInvocation,
    ToolResult,
    analyze_vision,
    detect_contradictions,
    predict_issues,
    recommend_action,
    create_decision_card,
)

__all__ = [
    # Server
    "MCPServer",
    "MCPRequest",
    "MCPResponse",
    "get_mcp_server",
    
    # Tools
    "SATOR_TOOLS",
    "ToolInvocation",
    "ToolResult",
    "analyze_vision",
    "detect_contradictions",
    "predict_issues",
    "recommend_action",
    "create_decision_card",
]
