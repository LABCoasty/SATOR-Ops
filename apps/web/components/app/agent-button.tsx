"use client"

<<<<<<< HEAD
import { useState, useRef, useEffect } from "react"
import { Bot, X, Send, FileText, Loader2, Terminal, CheckCircle, AlertTriangle } from "lucide-react"
=======
import { useState } from "react"
import Image from "next/image"
import { X, Send, Mic, FileText } from "lucide-react"
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import Link from "next/link"

// Map natural language to tool calls
const TOOL_MAPPINGS: Record<string, { tool: string; params?: Record<string, string> }> = {
  "explain current trust score": { tool: "explain_trust_score", params: { tag_id: "PT-001" } },
  "explain trust score": { tool: "explain_trust_score", params: { tag_id: "PT-001" } },
  "show contradictions": { tool: "list_contradictions" },
  "list contradictions": { tool: "list_contradictions" },
  "verify audit": { tool: "verify_audit_log" },
  "verify the audit log": { tool: "verify_audit_log" },
  "compile decision artifact": { tool: "create_decision_card" },
}

const suggestedActions = [
  { label: "Verify audit log", tool: "verify_audit_log", params: {} },
  { label: "List contradictions", tool: "list_contradictions", params: {} },
  { label: "Explain trust", tool: "explain_trust_score", params: { tag_id: "PT-001" } },
]

interface Message {
  role: "user" | "agent" | "tool"
  content: string
  toolName?: string
  isLoading?: boolean
  isError?: boolean
}

export function AgentButton() {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const invokeTool = async (toolName: string, params: Record<string, unknown> = {}) => {
    try {
      const response = await fetch(`${API_BASE}/api/leanmcp/invoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool_name: toolName, parameters: params }),
      })
      if (!response.ok) throw new Error(`API error: ${response.status}`)
      return await response.json()
    } catch (error) {
      throw error
    }
  }

  const formatToolResult = (toolName: string, result: unknown): string => {
    const data = result as Record<string, unknown>
    const r = data.result as Record<string, unknown>
    
    if (toolName === "verify_audit_log") {
      return `Audit: ${r?.integrity_status || "Unknown"} | Events: ${r?.event_count || 0}`
    }
    if (toolName === "list_contradictions") {
      return `Found ${r?.count || 0} contradictions`
    }
    if (toolName === "explain_trust_score") {
      if (r?.success === false) return `Tag not found`
      return `Trust: ${((r?.trust_score as number) * 100).toFixed(0)}% | State: ${r?.trust_state}`
    }
    return JSON.stringify(r || data, null, 2).slice(0, 200)
  }

  const interpretResult = (toolName: string, result: unknown): string => {
    const data = result as Record<string, unknown>
    const r = data.result as Record<string, unknown>
    
    if (toolName === "verify_audit_log") {
      return r?.verified 
        ? "Audit log verified - no tampering detected."
        : "Warning: Audit verification failed."
    }
    if (toolName === "list_contradictions") {
      const count = r?.count as number || 0
      return count === 0 
        ? "No active contradictions. Sensor readings are consistent."
        : `${count} contradiction(s) need attention.`
    }
    if (toolName === "explain_trust_score") {
      if (r?.success === false) return "Sensor not found. Try ingesting telemetry first."
      const score = r?.trust_score as number
      if (score >= 0.8) return "High trust - reliable for decisions."
      if (score >= 0.5) return "Moderate trust - verify before acting."
      return "Low trust - manual verification recommended."
    }
    return "Tool executed successfully."
  }

  const handleToolAction = async (toolName: string, params: Record<string, unknown> = {}, userMessage?: string) => {
    if (isProcessing) return
    setIsProcessing(true)
    
    if (userMessage) {
      setMessages(prev => [...prev, { role: "user", content: userMessage }])
    }
    
    setMessages(prev => [...prev, { role: "tool", content: `Running ${toolName}...`, toolName, isLoading: true }])
    
    try {
      const result = await invokeTool(toolName, params)
      
      setMessages(prev => {
        const newMessages = [...prev]
        const loadingIdx = newMessages.findIndex(m => m.isLoading && m.toolName === toolName)
        if (loadingIdx !== -1) {
          newMessages[loadingIdx] = {
            role: "tool",
            content: formatToolResult(toolName, result),
            toolName,
            isLoading: false,
          }
        }
        return newMessages
      })
      
      setMessages(prev => [...prev, { role: "agent", content: interpretResult(toolName, result) }])
    } catch (error) {
      setMessages(prev => {
        const newMessages = [...prev]
        const loadingIdx = newMessages.findIndex(m => m.isLoading && m.toolName === toolName)
        if (loadingIdx !== -1) {
          newMessages[loadingIdx] = {
            role: "tool",
            content: `Error: ${error instanceof Error ? error.message : "Unknown"}`,
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

  const handleSubmit = async (text: string) => {
    if (!text.trim() || isProcessing) return
    const lowerText = text.toLowerCase().trim()
    setInput("")
    
    for (const [phrase, mapping] of Object.entries(TOOL_MAPPINGS)) {
      if (lowerText.includes(phrase)) {
        await handleToolAction(mapping.tool, mapping.params || {}, text)
        return
      }
    }
    
    setMessages(prev => [
      ...prev,
      { role: "user", content: text },
      { role: "agent", content: "Try: 'verify audit log', 'list contradictions', or 'explain trust score'" },
    ])
  }

  const handleOpen = () => {
    setIsOpen(true)
    if (messages.length === 0) {
      setMessages([{
        role: "agent",
        content: "LeanMCP Agent ready. I can verify audits, list contradictions, explain trust scores, and more.",
      }])
    }
  }

  return (
    <>
      {/* Popup Chat Box */}
      {isOpen && (
<<<<<<< HEAD
        <div className="fixed bottom-24 right-6 w-[380px] rounded-lg border border-border bg-card shadow-xl z-50 flex flex-col max-h-[480px]">
=======
        <div 
          className="fixed bottom-24 right-6 w-[420px] rounded-lg shadow-xl z-50 flex flex-col max-h-[500px]"
          style={{ 
            backgroundColor: 'var(--surface0)',
            border: '1px solid var(--border0)',
          }}
        >
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
          {/* Header */}
          <div 
            className="flex items-center justify-between px-4 py-3 rounded-t-lg"
            style={{ 
              backgroundColor: 'var(--surface0)',
              borderBottom: '1px solid var(--border0)',
            }}
          >
            <div className="flex items-center gap-2">
<<<<<<< HEAD
              <Bot className="h-5 w-5 text-primary" />
              <span className="text-sm font-medium">LeanMCP Agent</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/20 text-primary">11 tools</span>
            </div>
            <div className="flex items-center gap-1">
              <Link href="/app/agent">
                <Button variant="ghost" size="sm" className="h-7 text-xs">
                  Full Page
                </Button>
              </Link>
              <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)} className="h-8 w-8 p-0">
                <X className="h-4 w-4" />
              </Button>
            </div>
=======
              {/* Agent orb image */}
              <Image
                src="/logosynagntwidget.png"
                alt="Logos"
                width={24}
                height={24}
                className="rounded-full"
              />
              <span 
                className="text-sm font-medium"
                style={{ fontFamily: 'var(--font-nav)', color: 'var(--textPrimary)' }}
              >
                Logos
              </span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)} className="h-8 w-8 p-0">
              <X className="h-4 w-4" style={{ color: 'var(--textSecondary)' }} />
            </Button>
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-auto p-3 space-y-2 min-h-[180px] max-h-[260px]">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
<<<<<<< HEAD
                  "rounded-md p-2 text-sm leading-relaxed",
                  msg.role === "agent" && "bg-muted text-muted-foreground",
                  msg.role === "user" && "bg-primary/10 text-foreground ml-4",
                  msg.role === "tool" && "bg-zinc-900 border border-zinc-700 font-mono text-xs",
                  msg.isError && "border-red-500/50",
=======
                  "rounded-md p-3 text-sm leading-relaxed",
                  msg.role === "agent" ? "" : "ml-4",
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
                )}
                style={{
                  fontFamily: 'var(--font-nav)',
                  backgroundColor: msg.role === "agent" ? 'var(--surface1)' : 'var(--trustMuted)',
                  color: 'var(--textPrimary)',
                }}
              >
                {msg.role === "tool" && (
                  <div className="flex items-center gap-1.5 mb-1 text-zinc-400 text-[10px]">
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
<<<<<<< HEAD
          <div className="border-t border-border p-3 space-y-2">
            <div className="flex flex-wrap gap-1.5">
              {suggestedActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleToolAction(action.tool, action.params, action.label)}
                  disabled={isProcessing}
                  className={cn(
                    "rounded-md border border-border bg-secondary px-2 py-1 text-xs hover:bg-muted transition-colors",
                    isProcessing && "opacity-50 cursor-not-allowed"
                  )}
=======
          <div className="p-3 space-y-3" style={{ borderTop: '1px solid var(--border0)' }}>
            <div className="flex flex-wrap gap-2">
              {suggestedActions.map((action) => (
                <button
                  key={action}
                  onClick={() => handleSubmit(action)}
                  className="rounded-md px-2 py-1 text-xs transition-colors"
                  style={{
                    fontFamily: 'var(--font-nav)',
                    backgroundColor: 'var(--surface1)',
                    border: '1px solid var(--border0)',
                    color: 'var(--textSecondary)',
                  }}
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
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
<<<<<<< HEAD
                placeholder="Ask about trust, contradictions..."
                disabled={isProcessing}
                className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
              />
              <Button size="sm" onClick={() => handleSubmit(input)} disabled={isProcessing} className="h-9 w-9 p-0">
                {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>

            <p className="text-[10px] text-muted-foreground flex items-center gap-1">
=======
                placeholder="Ask about the data..."
                className="flex-1 rounded-md px-3 py-2 text-sm placeholder:opacity-50 focus:outline-none focus:ring-1"
                style={{
                  fontFamily: 'var(--font-nav)',
                  backgroundColor: 'var(--bg0)',
                  border: '1px solid var(--border0)',
                  color: 'var(--textPrimary)',
                }}
              />
              <Button size="sm" variant="ghost" className="h-9 w-9 p-0">
                <Mic className="h-4 w-4" style={{ color: 'var(--textSecondary)' }} />
              </Button>
              <Button size="sm" onClick={() => handleSubmit(input)} className="h-9 w-9 p-0">
                <Send className="h-4 w-4" />
              </Button>
            </div>

            {/* Ground in evidence note */}
            <p 
              className="text-[10px] flex items-center gap-1"
              style={{ fontFamily: 'var(--font-nav)', color: 'var(--textTertiary)' }}
            >
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
              <FileText className="h-3 w-3" />
              Responses from LeanMCP tools
            </p>
          </div>
        </div>
      )}

      {/* Floating Button - Gradient Orb */}
      <button
        onClick={isOpen ? () => setIsOpen(false) : handleOpen}
<<<<<<< HEAD
        className="fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 z-50"
        aria-label={isOpen ? "Close assistant" : "Open LeanMCP agent"}
=======
        className="fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-full shadow-lg transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 z-50 overflow-hidden"
        style={{
          backgroundColor: 'var(--surface1)',
          boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
        }}
        aria-label={isOpen ? "Close assistant" : "Open operator assistant"}
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
      >
        {isOpen ? (
          <X className="h-6 w-6" style={{ color: 'var(--textPrimary)' }} />
        ) : (
<<<<<<< HEAD
          <>
            <Bot className="h-6 w-6" />
            <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-success text-[9px] font-bold text-success-foreground">
              MCP
            </span>
          </>
=======
          <Image
            src="/logosynagntwidget.png"
            alt="Logos"
            width={56}
            height={56}
            className="object-cover"
          />
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
        )}
      </button>
    </>
  )
}
