"""
LeanMCP Tools API - Expose MCP tools via REST endpoints.

These endpoints allow external systems and agents to invoke
SATOR decision tools directly via HTTP.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from ...integrations.leanmcp import (
    SATOR_TOOLS,
    get_mcp_server,
    MCPRequest,
    # Tools
    analyze_vision,
    detect_contradictions,
    predict_issues,
    recommend_action,
    create_decision_card,
    summarize_incident,
    explain_trust_score,
    verify_audit_log,
    get_state_at_time,
    list_contradictions,
    get_dispatch_draft,
)

router = APIRouter(prefix="/leanmcp", tags=["leanmcp-tools"])


# ============================================================================
# Request Models
# ============================================================================

class ToolInvokeRequest(BaseModel):
    """Request to invoke a tool by name"""
    tool_name: str
    parameters: Dict[str, Any] = {}


class VisionAnalysisRequest(BaseModel):
    """Request for vision analysis"""
    vision_frame: Dict[str, Any]


class ContradictionDetectRequest(BaseModel):
    """Request for contradiction detection"""
    vision_frame: Dict[str, Any]
    telemetry: Dict[str, Any]


class PredictIssuesRequest(BaseModel):
    """Request for issue prediction"""
    vision_frame: Dict[str, Any]
    telemetry: Dict[str, Any]
    history: Optional[List[Dict[str, Any]]] = None


class RecommendActionRequest(BaseModel):
    """Request for action recommendation"""
    incident_state: Dict[str, Any]
    evidence: Dict[str, Any]
    trust_score: float
    operator_answers: Optional[List[Dict[str, Any]]] = None


class CreateDecisionCardRequest(BaseModel):
    """Request for creating decision card"""
    incident_id: str
    findings: Dict[str, Any]
    operator_questions: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# Tool Discovery Endpoints
# ============================================================================

@router.get("/tools")
async def list_tools():
    """
    List all available LeanMCP tools.
    
    Returns tool names, descriptions, and parameter schemas.
    """
    tools = []
    for tool in SATOR_TOOLS:
        tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "category": "vision_decision" if tool["name"] in [
                "analyze_vision", "detect_contradictions", "predict_issues",
                "recommend_action", "create_decision_card"
            ] else "agent_command"
        })
    
    return {
        "tools": tools,
        "count": len(tools),
        "categories": {
            "vision_decision": "Vision and decision processing tools",
            "agent_command": "Agent command interface tools"
        }
    }


@router.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific tool."""
    for tool in SATOR_TOOLS:
        if tool["name"] == tool_name:
            # Get function signature for parameter info
            handler = tool["handler"]
            import inspect
            sig = inspect.signature(handler)
            params = []
            for param_name, param in sig.parameters.items():
                param_info = {
                    "name": param_name,
                    "required": param.default == inspect.Parameter.empty,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any"
                }
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = str(param.default)
                params.append(param_info)
            
            return {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": params,
                "docstring": handler.__doc__
            }
    
    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


# ============================================================================
# Generic Tool Invocation
# ============================================================================

@router.post("/invoke")
async def invoke_tool(request: ToolInvokeRequest):
    """
    Invoke any tool by name with parameters.
    
    This is the generic invocation endpoint for MCP-style tool calls.
    """
    # Find the tool
    tool_handler = None
    for tool in SATOR_TOOLS:
        if tool["name"] == request.tool_name:
            tool_handler = tool["handler"]
            break
    
    if not tool_handler:
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")
    
    try:
        result = tool_handler(**request.parameters)
        return {
            "success": True,
            "tool": request.tool_name,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


# ============================================================================
# Vision & Decision Tool Endpoints
# ============================================================================

@router.post("/analyze-vision")
async def api_analyze_vision(request: VisionAnalysisRequest):
    """Analyze vision frame from Overshoot."""
    result = analyze_vision(request.vision_frame)
    return {"success": True, "result": result}


@router.post("/detect-contradictions")
async def api_detect_contradictions(request: ContradictionDetectRequest):
    """Detect contradictions between vision and telemetry."""
    result = detect_contradictions(request.vision_frame, request.telemetry)
    return {"success": True, "contradictions": result, "count": len(result)}


@router.post("/predict-issues")
async def api_predict_issues(request: PredictIssuesRequest):
    """Predict potential issues."""
    result = predict_issues(request.vision_frame, request.telemetry, request.history)
    return {"success": True, "predictions": result, "count": len(result)}


@router.post("/recommend-action")
async def api_recommend_action(request: RecommendActionRequest):
    """Generate action recommendation."""
    result = recommend_action(
        request.incident_state,
        request.evidence,
        request.trust_score,
        request.operator_answers
    )
    return {"success": True, "recommendation": result}


@router.post("/create-decision-card")
async def api_create_decision_card(request: CreateDecisionCardRequest):
    """Create operator decision card."""
    result = create_decision_card(
        request.incident_id,
        request.findings,
        request.operator_questions
    )
    return {"success": True, "decision_card": result}


# ============================================================================
# Agent Command Tool Endpoints
# ============================================================================

@router.get("/incident/{incident_id}/summary")
async def api_summarize_incident(incident_id: str):
    """Summarize an incident with timeline and contradictions."""
    result = summarize_incident(incident_id)
    return result


@router.get("/trust/explain/{tag_id}")
async def api_explain_trust(tag_id: str):
    """Explain trust score for a sensor."""
    result = explain_trust_score(tag_id)
    return result


@router.get("/audit/verify")
async def api_verify_audit():
    """Verify integrity of the audit log."""
    result = verify_audit_log()
    return result


@router.get("/state")
async def api_get_state(t: str, scenario_id: Optional[str] = None):
    """
    Get reconstructed system state at a specific time.
    
    Args:
        t: Time string (ISO format, "2:00 PM", or seconds offset)
        scenario_id: Optional scenario ID
    """
    result = get_state_at_time(t, scenario_id)
    return result


@router.get("/contradictions")
async def api_list_contradictions(
    scenario_id: Optional[str] = None,
    severity: Optional[str] = None
):
    """List all active contradictions."""
    result = list_contradictions(scenario_id, severity)
    return result


@router.get("/dispatch/{incident_id}")
async def api_get_dispatch(incident_id: str):
    """Generate dispatch draft for field technician."""
    result = get_dispatch_draft(incident_id)
    return result


# ============================================================================
# MCP Server Status
# ============================================================================

@router.get("/status")
async def get_mcp_status():
    """Get LeanMCP server status."""
    server = get_mcp_server()
    capabilities = server.get_capabilities() if server else None
    return {
        "status": "running",
        "server_name": capabilities.server_name if capabilities else "sator-leanmcp",
        "protocol_version": capabilities.protocol_version if capabilities else "1.0",
        "tools_count": len(SATOR_TOOLS),
        "tools": [t["name"] for t in SATOR_TOOLS]
    }
