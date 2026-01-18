"use client"

import { useState, useRef, useEffect } from "react"
import { X, Send, Mic, FileText, Bot, Loader2, CheckCircle, AlertTriangle, Terminal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface AgentPanelProps {
  onClose: () => void
}

// Map natural language to tool calls
const TOOL_MAPPINGS: Record<string, { tool: string; params?: Record<string, string> }> = {
  "explain current trust score": { tool: "explain_trust_score", params: { tag_id: "PT-001" } },
  "explain trust score": { tool: "explain_trust_score", params: { tag_id: "PT-001" } },
  "show contradictions": { tool: "list_contradictions" },
  "list contradictions": { tool: "list_contradictions" },
  "verify audit": { tool: "verify_audit_log" },
  "verify the audit log": { tool: "verify_audit_log" },
  "verify audit log": { tool: "verify_audit_log" },
  "compile decision artifact": { tool: "create_decision_card" },
}

const suggestedActions = [
  { label: "Explain trust score", tool: "explain_trust_score", params: { tag_id: "PT-001" } },
  { label: "List contradictions", tool: "list_contradictions", params: {} },
  { label: "Verify audit log", tool: "verify_audit_log", params: {} },
  { label: "Get system state", tool: "get_state_at_time", params: { t: "now" } },
]

interface Message {
  role: "user" | "agent" | "tool"
  content: string
  toolName?: string
  toolResult?: unknown
  isLoading?: boolean
  isError?: boolean
}

export function AgentPanel({ onClose }: AgentPanelProps) {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      content:
        "Ready to assist. I have access to 11 LeanMCP tools for analyzing trust, contradictions, and incidents. Try asking me to explain a trust score or verify the audit log.",
    },
  ])
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const invokeTool = async (toolName: string, params: Record<string, unknown> = {}) => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    
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
      
      return await response.json()
    } catch (error) {
      throw error
    }
  }

  const handleToolAction = async (toolName: string, params: Record<string, unknown> = {}, userMessage?: string) => {
    if (isProcessing) return
    
    setIsProcessing(true)
    
    // Add user message if provided
    if (userMessage) {
      setMessages(prev => [...prev, { role: "user", content: userMessage }])
    }
    
    // Add loading message
    setMessages(prev => [...prev, { 
      role: "tool", 
      content: `Invoking ${toolName}...`, 
      toolName,
      isLoading: true 
    }])
    
    try {
      const result = await invokeTool(toolName, params)
      
      // Replace loading message with result
      setMessages(prev => {
        const newMessages = [...prev]
        const loadingIdx = newMessages.findIndex(m => m.isLoading && m.toolName === toolName)
        if (loadingIdx !== -1) {
          newMessages[loadingIdx] = {
            role: "tool",
            content: formatToolResult(toolName, result),
            toolName,
            toolResult: result,
            isLoading: false,
          }
        }
        return newMessages
      })
      
      // Add agent interpretation
      setMessages(prev => [...prev, {
        role: "agent",
        content: interpretResult(toolName, result),
      }])
      
    } catch (error) {
      setMessages(prev => {
        const newMessages = [...prev]
        const loadingIdx = newMessages.findIndex(m => m.isLoading && m.toolName === toolName)
        if (loadingIdx !== -1) {
          newMessages[loadingIdx] = {
            role: "tool",
            content: `Error invoking ${toolName}: ${error instanceof Error ? error.message : "Unknown error"}`,
            toolName,
            isLoading: false,
            isError: true,
          }
        }
        return newMessages
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const formatToolResult = (toolName: string, result: unknown): string => {
    const data = result as Record<string, unknown>
    
    if (toolName === "verify_audit_log") {
      const r = data.result as Record<string, unknown>
      return `Audit Verification: ${r?.integrity_status || "Unknown"}\nEvents: ${r?.event_count || 0}\nChain ID: ${r?.chain_id || "N/A"}`
    }
    
    if (toolName === "list_contradictions") {
      const r = data.result as Record<string, unknown>
      return `Found ${r?.count || 0} contradictions`
    }
    
    if (toolName === "explain_trust_score") {
      const r = data.result as Record<string, unknown>
      if (r?.success === false) {
        return `Tag not found: ${r?.error || "Unknown error"}`
      }
      return `Trust Score: ${r?.trust_score || "N/A"}\nState: ${r?.trust_state || "Unknown"}\nReason Codes: ${(r?.reason_codes as unknown[])?.length || 0}`
    }
    
    if (toolName === "get_state_at_time") {
      const r = data.result as Record<string, unknown>
      const state = r?.state as Record<string, unknown>
      return `State at ${r?.target_time || "now"}:\nMode: ${state?.operational_mode || "observe"}\nActive Incidents: ${state?.incident_count || 0}`
    }
    
    return JSON.stringify(data.result || data, null, 2).slice(0, 500)
  }

  const interpretResult = (toolName: string, result: unknown): string => {
    const data = result as Record<string, unknown>
    
    if (toolName === "verify_audit_log") {
      const r = data.result as Record<string, unknown>
      if (r?.verified) {
        return "The audit log hash chain is intact. No tampering detected - all decision records are cryptographically verified."
      }
      return "Warning: Audit log verification failed. This could indicate data tampering or corruption."
    }
    
    if (toolName === "list_contradictions") {
      const r = data.result as Record<string, unknown>
      const count = r?.count as number || 0
      if (count === 0) {
        return "No active contradictions detected. Sensor readings appear consistent."
      }
      return `Found ${count} contradiction(s) requiring attention. These represent discrepancies between expected and observed values.`
    }
    
    if (toolName === "explain_trust_score") {
      const r = data.result as Record<string, unknown>
      if (r?.success === false) {
        return "I couldn't find that sensor in the trust layer. Try checking the sensor ID or ingesting some telemetry data first."
      }
      const score = r?.trust_score as number
      if (score && score >= 0.8) {
        return "This sensor has high trust - readings are reliable for decision-making."
      } else if (score && score >= 0.5) {
        return "Moderate trust level - consider verification before taking irreversible actions."
      }
      return "Low trust score indicates potential sensor issues. Manual verification recommended."
    }
    
    return "Tool executed successfully. Let me know if you need more details."
  }

  const handleSubmit = async (text: string) => {
    if (!text.trim() || isProcessing) return
    
    const lowerText = text.toLowerCase().trim()
    setInput("")
    
    // Check for tool mappings
    for (const [phrase, mapping] of Object.entries(TOOL_MAPPINGS)) {
      if (lowerText.includes(phrase)) {
        await handleToolAction(mapping.tool, mapping.params || {}, text)
        return
      }
    }
    
    // Check for time-based queries
    const timeMatch = lowerText.match(/what happened at (\d{1,2}:\d{2}(?:\s*[ap]m)?)/i)
    if (timeMatch) {
      await handleToolAction("get_state_at_time", { t: timeMatch[1] }, text)
      return
    }
    
    // Check for incident summary
    const incidentMatch = lowerText.match(/summarize incident ([a-z0-9-]+)/i)
    if (incidentMatch) {
      await handleToolAction("summarize_incident", { incident_id: incidentMatch[1] }, text)
      return
    }
    
    // Default response for unrecognized commands
    setMessages(prev => [
      ...prev,
      { role: "user", content: text },
      {
        role: "agent",
        content: `I can help with that. Try one of my available tools:\n• "Explain trust score" - Analyze sensor reliability\n• "List contradictions" - Find data conflicts\n• "Verify audit log" - Check chain integrity\n• "What happened at 2:00 PM?" - Time travel to past state`,
      },
    ])
  }

  return (
    <aside className="w-96 border-l border-border bg-card flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium">LeanMCP Agent</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/20 text-primary font-medium">
            11 tools
          </span>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "rounded-md p-3 text-sm leading-relaxed",
              msg.role === "agent" && "bg-muted text-muted-foreground",
              msg.role === "user" && "bg-primary/10 text-foreground ml-4",
              msg.role === "tool" && "bg-zinc-900 border border-zinc-700 font-mono text-xs",
              msg.isError && "border-red-500/50 bg-red-950/20",
            )}
          >
            {msg.role === "tool" && (
              <div className="flex items-center gap-2 mb-2 text-zinc-400">
                {msg.isLoading ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : msg.isError ? (
                  <AlertTriangle className="h-3 w-3 text-red-400" />
                ) : (
                  <CheckCircle className="h-3 w-3 text-green-400" />
                )}
                <Terminal className="h-3 w-3" />
                <span>{msg.toolName}</span>
              </div>
            )}
            <div className="whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="border-t border-border p-3 space-y-3">
        <div className="flex flex-wrap gap-2">
          {suggestedActions.map((action) => (
            <button
              key={action.label}
              onClick={() => handleToolAction(action.tool, action.params, action.label)}
              disabled={isProcessing}
              className={cn(
                "rounded-md border border-border bg-secondary px-2 py-1 text-xs text-secondary-foreground hover:bg-muted transition-colors",
                isProcessing && "opacity-50 cursor-not-allowed"
              )}
            >
              {action.label}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit(input)}
            placeholder="Ask about trust, contradictions, audit..."
            disabled={isProcessing}
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
          />
          <Button 
            size="sm" 
            onClick={() => handleSubmit(input)} 
            disabled={isProcessing}
            className="h-9 w-9 p-0"
          >
            {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>

        {/* Ground in evidence note */}
        <p className="text-[10px] text-muted-foreground flex items-center gap-1">
          <FileText className="h-3 w-3" />
          All responses from LeanMCP tools - evidence-grounded
        </p>
      </div>
    </aside>
  )
}
