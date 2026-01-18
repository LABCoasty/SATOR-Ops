"use client"

import { useState } from "react"
import { Bot, X, Send, Mic, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const suggestedActions = [
  "Explain current trust score",
  "Show contradictions",
  "Navigate to anomaly",
  "Compile decision artifact",
]

export function AgentButton() {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Array<{ role: "user" | "agent"; content: string }>>([])

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

  const handleOpen = () => {
    setIsOpen(true)
    if (messages.length === 0) {
      setMessages([
        {
          role: "agent",
          content: "How can I help you? I can explain trust scores, navigate the timeline, identify contradictions, or compile decision artifacts.",
        },
      ])
    }
  }

  return (
    <>
      {/* Popup Chat Box */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-[420px] rounded-lg border border-border bg-card shadow-xl z-50 flex flex-col max-h-[500px]">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-4 py-3 rounded-t-lg bg-card">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              <span className="text-sm font-medium">Operator Assistant</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)} className="h-8 w-8 p-0">
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-auto p-4 space-y-4 min-h-[200px] max-h-[280px]">
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
        </div>
      )}

      {/* Floating Button */}
      <button
        onClick={isOpen ? () => setIsOpen(false) : handleOpen}
        className="fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 z-50"
        aria-label={isOpen ? "Close assistant" : "Open operator assistant"}
      >
        {isOpen ? (
          <X className="h-6 w-6" />
        ) : (
          <>
            <Bot className="h-6 w-6" />
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-success text-[10px] font-bold text-success-foreground">
              !
            </span>
          </>
        )}
      </button>
    </>
  )
}
