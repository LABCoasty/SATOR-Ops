"use client"

import type React from "react"
import { useState } from "react"
import { AppSidebar } from "./app-sidebar"
import { AppTopBar } from "./app-top-bar"
import { AgentPanel } from "./agent-panel"
import { AgentButton } from "./agent-button"

export type AppMode = "ingest" | "decision" | "artifact"

export function AppShell({ children }: { children: React.ReactNode }) {
  const [agentOpen, setAgentOpen] = useState(false)

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Left Sidebar Navigation */}
      <AppSidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Status Bar */}
        <AppTopBar onAgentToggle={() => setAgentOpen(!agentOpen)} agentOpen={agentOpen} />

        {/* Main Canvas with optional right panel */}
        <div className="flex flex-1 overflow-hidden relative">
          <main className="flex-1 overflow-auto p-6">{children}</main>

          {/* Agent Insight Panel */}
          {agentOpen && <AgentPanel onClose={() => setAgentOpen(false)} />}

          {!agentOpen && <AgentButton onClick={() => setAgentOpen(true)} />}
        </div>
      </div>
    </div>
  )
}
