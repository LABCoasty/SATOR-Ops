"use client"

import { useState } from "react"
import { X, Send, Mic, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface AgentPanelProps {
  onClose: () => void
}

const suggestedActions = [
  "Explain current trust score",
  "Show contradictions",
  "Navigate to anomaly at 14:32",
  "Compile decision artifact",
]

export function AgentPanel({ onClose }: AgentPanelProps) {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Array<{ role: "user" | "agent"; content: string }>>([
    {
      role: "agent",
      content:
        "Ready to assist. I can explain trust scores, navigate the timeline, identify contradictions, or compile decision artifacts. What do you need?",
    },
  ])

  const handleSubmit = (text: string) => {
    if (!text.trim()) return
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      {
        role: "agent",
        content: `Analyzing "${text.slice(0, 30)}..."—based on current telemetry and trust calculations, I can provide evidence-grounded insights. Would you like me to reference specific data points?`,
      },
    ])
    setInput("")
  }

  return (
    <aside className="w-80 border-l border-border bg-card flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
          <span className="text-sm font-medium">Operator Assistant</span>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "rounded-md p-3 text-sm leading-relaxed",
              msg.role === "agent" ? "bg-muted text-muted-foreground" : "bg-primary/10 text-foreground ml-4",
            )}
          >
            {msg.content}
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="border-t border-border p-3 space-y-3">
        <div className="flex flex-wrap gap-2">
          {suggestedActions.map((action) => (
            <button
              key={action}
              onClick={() => handleSubmit(action)}
              className="rounded-md border border-border bg-secondary px-2 py-1 text-xs text-secondary-foreground hover:bg-muted transition-colors"
            >
              {action}
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
            placeholder="Ask about the data..."
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <Button size="sm" variant="ghost" className="h-9 w-9 p-0">
            <Mic className="h-4 w-4" />
          </Button>
          <Button size="sm" onClick={() => handleSubmit(input)} className="h-9 w-9 p-0">
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {/* Ground in evidence note */}
        <p className="text-[10px] text-muted-foreground flex items-center gap-1">
          <FileText className="h-3 w-3" />
          All responses grounded in current evidence
        </p>
      </div>
    </aside>
  )
}
