"""
LeanMCP Server Implementation

MCP server for exposing SATOR tools via the Model Context Protocol.
"""

from typing import Any, Callable
from app.models.mcp import SATOR_MCP_TOOLS, MCPToolDefinition
from config import config


class MCPServer:
    """
    MCP server for SATOR Ops tools.
    
    Exposes tools via the MCP protocol for agent consumption.
    This is a simplified implementation - the full MCP server
    would use the mcp library for proper protocol handling.
    """
    
    def __init__(self):
        self._tools: dict[str, MCPToolDefinition] = {}
        self._handlers: dict[str, Callable] = {}
        self._enabled = config.enable_leanmcp
        
        # Register default tools
        for tool in SATOR_MCP_TOOLS:
            self._tools[tool.name] = tool
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def register_handler(self, tool_name: str, handler: Callable) -> None:
        """Register a handler function for a tool"""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        self._handlers[tool_name] = handler
    
    def get_tools(self) -> list[dict]:
        """Get all registered tools as JSON-serializable dicts"""
        return [tool.model_dump() for tool in self._tools.values()]
    
    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Execute a tool with the given arguments.
        
        Returns the tool result or an error response.
        """
        if not self._enabled:
            return {"error": "MCP integration is disabled"}
        
        if tool_name not in self._tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        handler = self._handlers.get(tool_name)
        if handler is None:
            return {"error": f"No handler registered for tool: {tool_name}"}
        
        try:
            result = await handler(**arguments)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
    
    def get_manifest(self) -> dict:
        """Get the MCP server manifest"""
        return {
            "name": "sator-ops",
            "version": "0.1.0",
            "description": "SATOR Ops Decision Infrastructure Tools",
            "tools": self.get_tools(),
        }


# Global server instance
_mcp_server: MCPServer | None = None


def get_mcp_server() -> MCPServer:
    """Get or create the MCP server instance"""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


async def setup_mcp_handlers(
    replay_engine,
    audit_ledger,
) -> MCPServer:
    """
    Set up MCP handlers with the actual engine implementations.
    
    This connects the MCP tools to the backend logic.
    """
    server = get_mcp_server()
    
    # Register handlers
    server.register_handler("list_contradictions", 
        lambda timestamp: replay_engine.get_state_at_t(timestamp))
    
    server.register_handler("explain_trust_score",
        lambda tag_id, timestamp=None: _explain_trust(replay_engine, tag_id, timestamp))
    
    server.register_handler("verify_audit",
        lambda: _verify_audit(audit_ledger))
    
    server.register_handler("get_state_at_t",
        lambda timestamp: replay_engine.get_state_at_t(timestamp))
    
    return server


async def _explain_trust(replay_engine, tag_id: str, timestamp: str | None) -> dict:
    """Handler for explain_trust_score tool"""
    from datetime import datetime
    query_time = timestamp or datetime.utcnow().isoformat()
    state = await replay_engine.get_state_at_t(query_time)
    
    trust_score = state.get("trust_scores", {}).get(tag_id, 1.0)
    reason_codes = state.get("active_reason_codes", {}).get(tag_id, [])
    
    return {
        "tag_id": tag_id,
        "trust_score": trust_score,
        "reason_codes": reason_codes,
    }


async def _verify_audit(audit_ledger) -> dict:
    """Handler for verify_audit tool"""
    from app.core.audit import ChainVerifier
    events = audit_ledger.get_events()
    verifier = ChainVerifier()
    result = verifier.verify_chain(events)
    
    return {
        "status": "PASS" if result.is_valid else "FAIL",
        "events_checked": result.events_checked,
        "root_hash": result.genesis_hash,
    }
