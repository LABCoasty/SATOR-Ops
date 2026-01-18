"""
LeanMCP Integration - MCP transport layer for SATOR decision tools.

Provides MCP-compliant tool server that exposes SATOR decision tools
for structured invocation by AI agents and backend services.

Tools Available:
---------------
Vision & Decision Tools:
  - analyze_vision: Extract insights from Overshoot vision output
  - detect_contradictions: Compare vision vs sensor telemetry
  - predict_issues: Predict potential problems
  - recommend_action: Generate action recommendations
  - create_decision_card: Package findings for operators

Agent Command Tools:
  - summarize_incident: Summarize incident with timeline
  - explain_trust_score: Explain trust score with reason codes
  - verify_audit_log: Verify hash chain integrity
  - get_state_at_time: Reconstruct state at specific time
  - list_contradictions: List all active contradictions
  - get_dispatch_draft: Generate dispatch draft for field tech
"""

from .server import MCPServer, MCPRequest, MCPResponse, get_mcp_server
from .tools import (
    SATOR_TOOLS,
    ToolInvocation,
    ToolResult,
    # Vision & Decision Tools
    analyze_vision,
    detect_contradictions,
    predict_issues,
    recommend_action,
    create_decision_card,
    # Agent Command Tools
    summarize_incident,
    explain_trust_score,
    verify_audit_log,
    get_state_at_time,
    list_contradictions,
    get_dispatch_draft,
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
    
    # Vision & Decision Tools
    "analyze_vision",
    "detect_contradictions",
    "predict_issues",
    "recommend_action",
    "create_decision_card",
    
    # Agent Command Tools
    "summarize_incident",
    "explain_trust_score",
    "verify_audit_log",
    "get_state_at_time",
    "list_contradictions",
    "get_dispatch_draft",
]
