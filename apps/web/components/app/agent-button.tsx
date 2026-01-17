"use client"

import { Bot } from "lucide-react"

interface AgentButtonProps {
  onClick: () => void
}

export function AgentButton({ onClick }: AgentButtonProps) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      aria-label="Open operator assistant"
    >
      <Bot className="h-6 w-6" />
      <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-success text-[10px] font-bold text-success-foreground">
        !
      </span>
    </button>
  )
}
