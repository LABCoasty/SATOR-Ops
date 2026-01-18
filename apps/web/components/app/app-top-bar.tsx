"use client"

import { useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { Radio, GitBranch, FileOutput, Bot, Wifi, WifiOff, ChevronDown, Video, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu"

const modes = [
  { path: "/app/ingest", label: "Data Ingest", icon: Radio, color: "text-chart-2" },
  { path: "/app/decision", label: "Decision / Trust", icon: GitBranch, color: "text-primary" },
  { path: "/app/artifact", label: "Artifact Creation", icon: FileOutput, color: "text-accent" },
  { path: "/app/receipt", label: "Artifact Creation", icon: FileOutput, color: "text-accent" },
  { path: "/app/vision", label: "Vision Monitoring", icon: Video, color: "text-primary" },
]

interface AppTopBarProps {
  onAgentToggle: () => void
  agentOpen: boolean
  onScenario2?: () => void
  scenario2Loading?: boolean
}

export function AppTopBar({ onAgentToggle, agentOpen, onScenario2, scenario2Loading }: AppTopBarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const currentMode = modes.find((m) => pathname.startsWith(m.path)) || modes[0]

  // Simulated system status
  const systemStatus = {
    connected: true,
    sources: 12,
    lastSync: "2s ago",
  }

  const handleScenario1 = () => {
    router.push("/app/ingest")
  }

  const handleScenario2 = () => {
    if (onScenario2) {
      onScenario2()
    } else {
      router.push("/app/vision")
    }
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4">
      {/* Left: Mode Indicator with Scenario Dropdown */}
      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button 
              className={cn(
                "flex items-center gap-2 rounded-md bg-secondary px-3 py-1.5 hover:bg-secondary/80 transition-colors cursor-pointer",
                currentMode.color
              )}
            >
              <currentMode.icon className="h-4 w-4" />
              <span className="text-sm font-medium">{currentMode.label}</span>
              <ChevronDown className="h-3 w-3 opacity-60" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Select Scenario
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleScenario1} className="cursor-pointer">
              <Radio className="h-4 w-4 mr-2 text-chart-2" />
              <div>
                <div className="font-medium">Scenario 1</div>
                <div className="text-xs text-muted-foreground">Fixed CSV/JSON data processing</div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={handleScenario2} 
              disabled={scenario2Loading}
              className="cursor-pointer"
            >
              {scenario2Loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin text-primary" />
              ) : (
                <Video className="h-4 w-4 mr-2 text-primary" />
              )}
              <div>
                <div className="font-medium">Scenario 2</div>
                <div className="text-xs text-muted-foreground">
                  {scenario2Loading ? "Processing video with Overshoot AI..." : "Live video analysis (Overshoot.ai)"}
                </div>
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

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
