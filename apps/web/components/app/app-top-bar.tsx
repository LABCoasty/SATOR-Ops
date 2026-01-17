"use client"

import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Radio, GitBranch, FileOutput, Bot, Wifi, WifiOff } from "lucide-react"
import { Button } from "@/components/ui/button"

const modes = [
  { path: "/app/ingest", label: "Data Ingest", icon: Radio, color: "text-chart-2" },
  { path: "/app/decision", label: "Decision / Trust", icon: GitBranch, color: "text-primary" },
  { path: "/app/artifact", label: "Artifact Creation", icon: FileOutput, color: "text-accent" },
  { path: "/app/receipt", label: "Artifact Creation", icon: FileOutput, color: "text-accent" },
]

interface AppTopBarProps {
  onAgentToggle: () => void
  agentOpen: boolean
}

export function AppTopBar({ onAgentToggle, agentOpen }: AppTopBarProps) {
  const pathname = usePathname()
  const currentMode = modes.find((m) => pathname.startsWith(m.path)) || modes[0]

  // Simulated system status
  const systemStatus = {
    connected: true,
    sources: 12,
    lastSync: "2s ago",
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4">
      {/* Left: Mode Indicator */}
      <div className="flex items-center gap-4">
        <div className={cn("flex items-center gap-2 rounded-md bg-secondary px-3 py-1.5", currentMode.color)}>
          <currentMode.icon className="h-4 w-4" />
          <span className="text-sm font-medium">{currentMode.label}</span>
        </div>

        {/* Mode selector pills */}
        <div className="hidden md:flex items-center gap-1 rounded-md border border-border p-1">
          {modes.slice(0, 3).map((mode) => {
            const isActive = pathname.startsWith(mode.path)
            return (
              <div
                key={mode.path}
                className={cn(
                  "flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium transition-colors",
                  isActive ? "bg-muted text-foreground" : "text-muted-foreground",
                )}
              >
                <mode.icon className="h-3 w-3" />
                <span className="hidden lg:inline">{mode.label.split(" ")[0]}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Right: Status & Agent */}
      <div className="flex items-center gap-4">
        {/* System Status */}
        <div className="hidden sm:flex items-center gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            {systemStatus.connected ? (
              <Wifi className="h-3.5 w-3.5 text-success" />
            ) : (
              <WifiOff className="h-3.5 w-3.5 text-destructive" />
            )}
            <span>{systemStatus.sources} sources</span>
          </div>
          <span className="text-border">|</span>
          <span>Synced {systemStatus.lastSync}</span>
        </div>

        {/* Agent Toggle */}
        <Button variant={agentOpen ? "default" : "outline"} size="sm" onClick={onAgentToggle} className="gap-2">
          <Bot className="h-4 w-4" />
          <span className="hidden sm:inline">Agent</span>
        </Button>
      </div>
    </header>
  )
}
