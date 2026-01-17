"""
LeanMCP Server - MCP transport layer for SATOR decision tools.

Implements MCP (Model Context Protocol) compliant server that exposes
SATOR decision tools for structured invocation.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
from enum import Enum

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


# ============================================================================
# MCP Protocol Models
# ============================================================================

class MCPToolSchema(BaseModel):
    """MCP-compliant tool schema."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    returns: Dict[str, Any]  # JSON Schema for return value


class MCPRequest(BaseModel):
    """MCP tool invocation request."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MCPResponse(BaseModel):
    """MCP tool invocation response."""
    request_id: str
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MCPCapabilities(BaseModel):
    """Server capabilities announcement."""
    protocol_version: str = "1.0"
    server_name: str = "sator-leanmcp"
    tools: List[MCPToolSchema]
    supports_streaming: bool = False
    supports_batch: bool = True


# ============================================================================
# MCP Server
# ============================================================================

class MCPServer:
    """
    LeanMCP Server for SATOR decision tools.
    
    Implements MCP-compliant tool server that:
    - Registers SATOR decision tools
    - Handles tool invocations
    - Returns structured outputs
    - Logs all invocations for audit
    """
    
    def __init__(self):
        """Initialize the MCP server."""
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, MCPToolSchema] = {}
        self._invocation_log: List[Dict[str, Any]] = []
        
        # Register default SATOR tools
        self._register_default_tools()
    
    # ========================================================================
    # Tool Registration
    # ========================================================================
    
    def _register_default_tools(self):
        """Register the default SATOR decision tools."""
        
        # Tool 1: analyze_vision
        self.register_tool(
            name="analyze_vision",
            handler=analyze_vision,
            description="Extract actionable insights from Overshoot vision output",
            parameters={
                "type": "object",
                "properties": {
                    "vision_frame": {
                        "type": "object",
                        "description": "VisionFrame from Overshoot"
                    }
                },
                "required": ["vision_frame"]
            },
            returns={
                "type": "object",
                "properties": {
                    "equipment_states": {"type": "array"},
                    "operator_positions": {"type": "array"},
                    "safety_flags": {"type": "array"},
                    "summary": {"type": "string"}
                }
            }
        )
        
        # Tool 2: detect_contradictions
        self.register_tool(
            name="detect_contradictions",
            handler=detect_contradictions,
            description="Compare vision observations against sensor telemetry to find contradictions",
            parameters={
                "type": "object",
                "properties": {
                    "vision_frame": {
                        "type": "object",
                        "description": "VisionFrame from Overshoot"
                    },
                    "telemetry": {
                        "type": "object",
                        "description": "Current sensor readings by tag_id"
                    }
                },
                "required": ["vision_frame", "telemetry"]
            },
            returns={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "contradiction_id": {"type": "string"},
                        "reason_code": {"type": "string"},
                        "description": {"type": "string"},
                        "confidence": {"type": "number"}
                    }
                }
            }
        )
        
        # Tool 3: predict_issues
        self.register_tool(
            name="predict_issues",
            handler=predict_issues,
            description="Predict potential issues before they occur based on vision and telemetry",
            parameters={
                "type": "object",
                "properties": {
                    "vision_frame": {
                        "type": "object",
                        "description": "VisionFrame from Overshoot"
                    },
                    "telemetry": {
                        "type": "object",
                        "description": "Current sensor readings"
                    },
                    "history": {
                        "type": "array",
                        "description": "Historical telemetry readings"
                    }
                },
                "required": ["vision_frame", "telemetry"]
            },
            returns={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "prediction_id": {"type": "string"},
                        "issue_type": {"type": "string"},
                        "confidence": {"type": "number"},
                        "explanation": {"type": "string"},
                        "recommended_action": {"type": "string"}
                    }
                }
            }
        )
        
        # Tool 4: recommend_action
        self.register_tool(
            name="recommend_action",
            handler=recommend_action,
            description="Generate bounded action recommendations with rationale",
            parameters={
                "type": "object",
                "properties": {
                    "incident_state": {
                        "type": "object",
                        "description": "Current incident state"
                    },
                    "evidence": {
                        "type": "object",
                        "description": "Evidence bundle (contradictions, predictions, etc.)"
                    },
                    "trust_score": {
                        "type": "number",
                        "description": "Current trust score (0-1)"
                    },
                    "operator_answers": {
                        "type": "array",
                        "description": "Answers from operator questions"
                    }
                },
                "required": ["incident_state", "evidence", "trust_score"]
            },
            returns={
                "type": "object",
                "properties": {
                    "recommended_action": {"type": "string"},
                    "confidence": {"type": "number"},
                    "rationale": {"type": "string"},
                    "alternatives": {"type": "array"},
                    "follow_up_questions": {"type": "array"}
                }
            }
        )
        
        # Tool 5: create_decision_card
        self.register_tool(
            name="create_decision_card",
            handler=create_decision_card,
            description="Package all findings into operator-ready decision card",
            parameters={
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "Incident ID"
                    },
                    "findings": {
                        "type": "object",
                        "description": "Analysis findings (contradictions, predictions, recommendations)"
                    },
                    "operator_questions": {
                        "type": "array",
                        "description": "Questions to ask the operator"
                    }
                },
                "required": ["incident_id", "findings"]
            },
            returns={
                "type": "object",
                "properties": {
                    "card_id": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "predictions": {"type": "array"},
                    "contradictions": {"type": "array"},
                    "allowed_actions": {"type": "array"},
                    "questions": {"type": "array"}
                }
            }
        )
    
    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str,
        parameters: Dict[str, Any],
        returns: Dict[str, Any]
    ):
        """
        Register a tool with the MCP server.
        
        Args:
            name: Tool name
            handler: Function to handle invocations
            description: Tool description
            parameters: JSON Schema for parameters
            returns: JSON Schema for return value
        """
        self._tools[name] = handler
        self._tool_schemas[name] = MCPToolSchema(
            name=name,
            description=description,
            parameters=parameters,
            returns=returns
        )
    
    # ========================================================================
    # Tool Invocation
    # ========================================================================
    
    def invoke(self, request: MCPRequest) -> MCPResponse:
        """
        Invoke a tool.
        
        Args:
            request: MCP request with tool name and parameters
            
        Returns:
            MCPResponse with result or error
        """
        start_time = datetime.utcnow()
        
        # Validate tool exists
        if request.tool_name not in self._tools:
            return MCPResponse(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error=f"Tool '{request.tool_name}' not found"
            )
        
        try:
            # Invoke tool
            handler = self._tools[request.tool_name]
            result = handler(**request.parameters)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log invocation
            self._log_invocation(request, result, None, execution_time_ms)
            
            return MCPResponse(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log error
            self._log_invocation(request, None, str(e), execution_time_ms)
            
            return MCPResponse(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms
            )
    
    def invoke_batch(self, requests: List[MCPRequest]) -> List[MCPResponse]:
        """Invoke multiple tools in sequence."""
        return [self.invoke(req) for req in requests]
    
    def _log_invocation(
        self,
        request: MCPRequest,
        result: Any,
        error: Optional[str],
        execution_time_ms: float
    ):
        """Log tool invocation for audit."""
        self._invocation_log.append({
            "request_id": request.request_id,
            "tool_name": request.tool_name,
            "timestamp": request.timestamp.isoformat(),
            "parameters": request.parameters,
            "success": error is None,
            "error": error,
            "execution_time_ms": execution_time_ms
        })
    
    # ========================================================================
    # Server Info
    # ========================================================================
    
    def get_capabilities(self) -> MCPCapabilities:
        """Get server capabilities and tool list."""
        return MCPCapabilities(
            tools=list(self._tool_schemas.values())
        )
    
    def get_tool_schema(self, tool_name: str) -> Optional[MCPToolSchema]:
        """Get schema for a specific tool."""
        return self._tool_schemas.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List available tool names."""
        return list(self._tools.keys())
    
    def get_invocation_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent invocation log."""
        return self._invocation_log[-limit:]


# ============================================================================
# Singleton instance
# ============================================================================

_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Get the singleton MCPServer instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server
