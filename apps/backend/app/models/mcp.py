"""
MCP Tool Schema Models

Defines tool schemas for LeanMCP integration (Primary Sponsor).
"""

from pydantic import BaseModel, Field


class MCPToolDefinition(BaseModel):
    """
    Definition of an MCP tool for the LeanMCP registry.
    
    Tools are exposed via MCP protocol for external consumption by agents.
    """
    name: str = Field(..., description="Tool name (snake_case)")
    description: str = Field(..., description="Human-readable description")
    input_schema: dict = Field(..., description="JSON Schema for parameters")


# SATOR Ops MCP Tools
SATOR_MCP_TOOLS = [
    MCPToolDefinition(
        name="list_contradictions",
        description="List active sensor contradictions at a given timestamp. Returns conflicts where sensors that should agree are in disagreement.",
        input_schema={
            "type": "object",
            "properties": {
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "ISO8601 timestamp to query"
                }
            },
            "required": ["timestamp"]
        }
    ),
    MCPToolDefinition(
        name="explain_trust_score",
        description="Explain the trust score and active reason codes for a specific sensor. Provides detailed breakdown of why the sensor is trusted, degraded, or quarantined.",
        input_schema={
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "Sensor/tag identifier"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Optional timestamp (defaults to current)"
                }
            },
            "required": ["tag_id"]
        }
    ),
    MCPToolDefinition(
        name="verify_audit",
        description="Verify the integrity of the hash-chained audit log. Returns verification status and any detected tampering.",
        input_schema={
            "type": "object",
            "properties": {
                "start_event_id": {
                    "type": "string",
                    "description": "Optional starting event ID (defaults to genesis)"
                },
                "end_event_id": {
                    "type": "string",
                    "description": "Optional ending event ID (defaults to latest)"
                }
            }
        }
    ),
    MCPToolDefinition(
        name="get_state_at_t",
        description="Reconstruct the complete system belief state at a specific timestamp. Returns telemetry values, trust scores, active contradictions, and operational mode.",
        input_schema={
            "type": "object",
            "properties": {
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "ISO8601 timestamp to reconstruct"
                }
            },
            "required": ["timestamp"]
        }
    ),
    MCPToolDefinition(
        name="get_incident_summary",
        description="Get a summary of an incident including timeline of events and key contradictions.",
        input_schema={
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                    "description": "Incident identifier"
                }
            },
            "required": ["incident_id"]
        }
    ),
    MCPToolDefinition(
        name="get_decision_receipt",
        description="Retrieve a decision receipt by ID. Returns the complete defensible record of a decision.",
        input_schema={
            "type": "object",
            "properties": {
                "receipt_id": {
                    "type": "string",
                    "description": "Decision receipt identifier"
                }
            },
            "required": ["receipt_id"]
        }
    ),
]


def get_tools_as_json() -> list[dict]:
    """Export tools as JSON-serializable list for MCP registration"""
    return [tool.model_dump() for tool in SATOR_MCP_TOOLS]
