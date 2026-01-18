"use client"

import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { Radio, GitBranch, FileOutput, Wifi, WifiOff, ChevronDown, Video, Loader2 } from "lucide-react"
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
  onScenario1?: () => void
  onScenario2?: () => void
  onScenario3?: () => void
  onScenario4?: () => void
  scenario1Loading?: boolean
  scenario2Loading?: boolean
  scenario3Loading?: boolean
  scenario4Loading?: boolean
}

export function AppTopBar({ onScenario1, onScenario2, onScenario3, onScenario4, scenario1Loading, scenario2Loading, scenario3Loading, scenario4Loading }: AppTopBarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const currentMode = modes.find((m) => pathname.startsWith(m.path)) || modes[0]

  // Simulated system status
  const systemStatus = {
    connected: true,
    sources: 12,
    lastSync: "2s ago",
  }

  const isAnyLoading = scenario1Loading || scenario2Loading || scenario3Loading || scenario4Loading

  const handleScenario1 = () => {
    router.push("/app/ingest")
    if (onScenario1) {
      onScenario1()
    }
  }

  const handleScenario2 = () => {
    router.push("/app/ingest")
    if (onScenario2) {
      onScenario2()
    }
  }

  const handleScenario3 = () => {
    router.push("/app/ingest")
    if (onScenario3) {
      onScenario3()
    }
  }

  const handleScenario4 = () => {
    router.push("/app/ingest")
    if (onScenario4) {
      onScenario4()
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
            <DropdownMenuItem 
              onClick={handleScenario1} 
              disabled={isAnyLoading}
              className="cursor-pointer"
            >
              {scenario1Loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin text-chart-2" />
              ) : (
                <Radio className="h-4 w-4 mr-2 text-chart-2" />
              )}
              <div>
                <div className="font-medium">Scenario 1: Valve Incident</div>
                <div className="text-xs text-muted-foreground">
                  {scenario1Loading ? "Starting 20s simulation..." : "20s telemetry simulation with decisions"}
                </div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={handleScenario2} 
              disabled={isAnyLoading}
              className="cursor-pointer"
            >
              {scenario2Loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin text-primary" />
              ) : (
                <Video className="h-4 w-4 mr-2 text-primary" />
              )}
              <div>
                <div className="font-medium">Scenario 2: Oil Rig Analysis</div>
                <div className="text-xs text-muted-foreground">
                  {scenario2Loading ? "Starting 20s simulation..." : "20s AI vision simulation with decisions"}
                </div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={handleScenario3} 
              disabled={isAnyLoading}
              className="cursor-pointer"
            >
              {scenario3Loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin text-blue-500" />
              ) : (
                <Video className="h-4 w-4 mr-2 text-blue-500" />
              )}
              <div>
                <div className="font-medium">Scenario 3: Water Pipe Leakage</div>
                <div className="text-xs text-muted-foreground">
                  {scenario3Loading ? "Starting 20s simulation..." : "20s water infrastructure monitoring"}
                </div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={handleScenario4} 
              disabled={isAnyLoading}
              className="cursor-pointer"
            >
              {scenario4Loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin text-orange-500" />
              ) : (
                <Video className="h-4 w-4 mr-2 text-orange-500" />
              )}
              <div>
                <div className="font-medium">Scenario 4: Data Center Arc Flash</div>
                <div className="text-xs text-muted-foreground">
                  {scenario4Loading ? "Starting 20s simulation..." : "20s electrical hazard monitoring"}
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

      {/* Right: Status */}
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
      </div>
    </header>
  )
}
