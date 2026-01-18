"use client"

import { useState, useEffect } from "react"
import { Bot, Terminal, CheckCircle, AlertTriangle, Loader2, Play, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface Tool {
  name: string
  description: string
  category: string
}

interface ToolResult {
  success: boolean
  tool: string
  result: unknown
}

export default function AgentPage() {
  const [tools, setTools] = useState<Tool[]>([])
  const [selectedTool, setSelectedTool] = useState<string | null>(null)
  const [toolParams, setToolParams] = useState<Record<string, string>>({})
  const [result, setResult] = useState<ToolResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [serverStatus, setServerStatus] = useState<"checking" | "online" | "offline">("checking")

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  // Fetch available tools on mount
  useEffect(() => {
    fetchTools()
    checkServerStatus()
  }, [])

  const checkServerStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/leanmcp/status`)
      if (response.ok) {
        setServerStatus("online")
      } else {
        setServerStatus("offline")
      }
    } catch {
      setServerStatus("offline")
    }
  }

  const fetchTools = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/leanmcp/tools`)
      if (response.ok) {
        const data = await response.json()
        setTools(data.tools || [])
      }
    } catch (err) {
      console.error("Failed to fetch tools:", err)
    }
  }

  const invokeTool = async (toolName: string, params: Record<string, unknown>) => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE}/api/leanmcp/invoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool_name: toolName,
          parameters: params,
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setIsLoading(false)
    }
  }

  // Tool-specific parameter definitions
  const getToolParams = (toolName: string): { name: string; placeholder: string; required: boolean }[] => {
    const paramDefs: Record<string, { name: string; placeholder: string; required: boolean }[]> = {
      summarize_incident: [{ name: "incident_id", placeholder: "INC-001", required: true }],
      explain_trust_score: [{ name: "tag_id", placeholder: "PT-001", required: true }],
      get_state_at_time: [
        { name: "time_str", placeholder: "2:00 PM or 2024-01-15T14:00:00", required: true },
        { name: "scenario_id", placeholder: "Optional scenario ID", required: false },
      ],
      list_contradictions: [
        { name: "scenario_id", placeholder: "Optional scenario ID", required: false },
        { name: "severity", placeholder: "low, medium, high, critical", required: false },
      ],
      get_dispatch_draft: [{ name: "incident_id", placeholder: "INC-001", required: true }],
      analyze_vision: [{ name: "vision_frame", placeholder: '{"equipment_states": [...]}', required: true }],
      detect_contradictions: [
        { name: "vision_frame", placeholder: '{"equipment_states": [...]}', required: true },
        { name: "telemetry", placeholder: '{"PT-001": {"value": 100}}', required: true },
      ],
    }
    return paramDefs[toolName] || []
  }

  const handleRunTool = () => {
    if (!selectedTool) return

    // Parse JSON params if needed
    const params: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(toolParams)) {
      if (!value) continue
      try {
        // Try to parse as JSON first
        params[key] = JSON.parse(value)
      } catch {
        // If not JSON, use as string
        params[key] = value
      }
    }

    invokeTool(selectedTool, params)
  }

  const visionTools = tools.filter((t) => t.category === "vision_decision")
  const agentTools = tools.filter((t) => t.category === "agent_command")

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Bot className="h-6 w-6 text-primary" />
              LeanMCP Agent Tools
            </h1>
            <p className="text-muted-foreground mt-1">
              Invoke MCP tools directly for decision support and system analysis
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm",
                serverStatus === "online" && "bg-green-500/20 text-green-400",
                serverStatus === "offline" && "bg-red-500/20 text-red-400",
                serverStatus === "checking" && "bg-yellow-500/20 text-yellow-400"
              )}
            >
              <div
                className={cn(
                  "h-2 w-2 rounded-full",
                  serverStatus === "online" && "bg-green-400",
                  serverStatus === "offline" && "bg-red-400",
                  serverStatus === "checking" && "bg-yellow-400 animate-pulse"
                )}
              />
              {serverStatus === "checking" ? "Checking..." : serverStatus === "online" ? "Server Online" : "Server Offline"}
            </div>
            <Button variant="outline" size="sm" onClick={() => { checkServerStatus(); fetchTools(); }}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Tool Selection */}
          <div className="space-y-4">
            {/* Vision & Decision Tools */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Vision & Decision Tools</CardTitle>
                <CardDescription>Process Overshoot vision data and generate decisions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {visionTools.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Loading tools...</p>
                ) : (
                  visionTools.map((tool) => (
                    <button
                      key={tool.name}
                      onClick={() => {
                        setSelectedTool(tool.name)
                        setToolParams({})
                        setResult(null)
                        setError(null)
                      }}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded-md border transition-colors",
                        selectedTool === tool.name
                          ? "border-primary bg-primary/10"
                          : "border-transparent hover:bg-muted"
                      )}
                    >
                      <div className="font-medium text-sm">{tool.name}</div>
                      <div className="text-xs text-muted-foreground">{tool.description}</div>
                    </button>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Agent Command Tools */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Agent Command Tools</CardTitle>
                <CardDescription>Query system state, trust, and audit logs</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {agentTools.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Loading tools...</p>
                ) : (
                  agentTools.map((tool) => (
                    <button
                      key={tool.name}
                      onClick={() => {
                        setSelectedTool(tool.name)
                        setToolParams({})
                        setResult(null)
                        setError(null)
                      }}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded-md border transition-colors",
                        selectedTool === tool.name
                          ? "border-primary bg-primary/10"
                          : "border-transparent hover:bg-muted"
                      )}
                    >
                      <div className="font-medium text-sm">{tool.name}</div>
                      <div className="text-xs text-muted-foreground">{tool.description}</div>
                    </button>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Tool Invocation Panel */}
          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Terminal className="h-5 w-5" />
                  {selectedTool ? selectedTool : "Select a Tool"}
                </CardTitle>
                <CardDescription>
                  {selectedTool
                    ? tools.find((t) => t.name === selectedTool)?.description
                    : "Choose a tool from the left to invoke it"}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedTool && (
                  <>
                    {/* Parameters */}
                    <div className="space-y-3">
                      {getToolParams(selectedTool).map((param) => (
                        <div key={param.name}>
                          <label className="text-sm font-medium">
                            {param.name}
                            {param.required && <span className="text-red-400 ml-1">*</span>}
                          </label>
                          <input
                            type="text"
                            value={toolParams[param.name] || ""}
                            onChange={(e) =>
                              setToolParams((prev) => ({ ...prev, [param.name]: e.target.value }))
                            }
                            placeholder={param.placeholder}
                            className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                          />
                        </div>
                      ))}
                      {getToolParams(selectedTool).length === 0 && (
                        <p className="text-sm text-muted-foreground">No parameters required</p>
                      )}
                    </div>

                    {/* Run Button */}
                    <Button
                      onClick={handleRunTool}
                      disabled={isLoading || serverStatus !== "online"}
                      className="w-full"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-2" />
                          Run Tool
                        </>
                      )}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Result Panel */}
            {(result || error) && (
              <Card className={cn(error ? "border-red-500/50" : "border-green-500/50")}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    {error ? (
                      <>
                        <AlertTriangle className="h-5 w-5 text-red-400" />
                        Error
                      </>
                    ) : (
                      <>
                        <CheckCircle className="h-5 w-5 text-green-400" />
                        Result
                      </>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-zinc-900 rounded-md p-4 overflow-auto text-xs font-mono text-zinc-300 max-h-96">
                    {error ? error : JSON.stringify(result, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Quick Actions</CardTitle>
            <CardDescription>Common tool invocations with pre-filled parameters</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => invokeTool("verify_audit_log", {})}
                disabled={isLoading}
              >
                Verify Audit Log
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => invokeTool("list_contradictions", {})}
                disabled={isLoading}
              >
                List All Contradictions
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => invokeTool("get_state_at_time", { time_str: "now" })}
                disabled={isLoading}
              >
                Get Current State
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => invokeTool("explain_trust_score", { tag_id: "PT-001" })}
                disabled={isLoading}
              >
                Explain PT-001 Trust
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
