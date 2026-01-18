"use client"

import { useState, useRef } from "react"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { Radio, GitBranch, FileOutput, Wifi, WifiOff, ChevronDown, Video, Loader2, Database, Upload, FileSpreadsheet, Server, History, Gauge } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

const modes = [
  { path: "/app/ingest", label: "Simulate scenario", icon: Radio, color: "text-chart-2" },
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
  
  // Data ingest dialog state
  const [showIngestDialog, setShowIngestDialog] = useState(false)
  const [ingestType, setIngestType] = useState<string>("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

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

  const handleOpenIngestDialog = (type: string) => {
    setIngestType(type)
    setSelectedFile(null)
    setShowIngestDialog(true)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleImportAndRun = async () => {
    setIsImporting(true)
    
    // Simulate file processing delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    setIsImporting(false)
    setShowIngestDialog(false)
    setSelectedFile(null)
    
    // Navigate and run Scenario 1
    router.push("/app/ingest")
    if (onScenario1) {
      onScenario1()
    }
  }

  const ingestTypeLabels: Record<string, string> = {
    sensors: "Live Sensor Feed",
    csv: "CSV/JSON File",
    historian: "Historian Data",
    scada: "SCADA System",
  }

  return (
    <header 
      className="flex h-14 items-center justify-between px-4"
      style={{ 
        backgroundColor: 'var(--surface0)',
        borderBottom: '1px solid var(--border0)',
      }}
    >
      {/* Left: Mode Indicator with Scenario Dropdown */}
      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button 
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-1.5 transition-colors cursor-pointer",
                currentMode.color
              )}
              style={{
                fontFamily: 'var(--font-nav)',
                backgroundColor: 'var(--surface1)',
              }}
            >
              <span className="text-sm font-medium">{currentMode.label}</span>
              <ChevronDown className="h-3 w-3 opacity-60" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuLabel className="text-xs" style={{ color: 'var(--textTertiary)' }}>
              Select Scenario
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleScenario1}
              disabled={isAnyLoading}
              className="cursor-pointer"
            >
              {scenario1Loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" style={{ color: 'var(--warning)' }} />
              ) : (
                <Radio className="h-4 w-4 mr-2" style={{ color: 'var(--warning)' }} />
              )}
              <div>
                <div className="font-medium" style={{ fontFamily: 'var(--font-nav)' }}>Scenario 1: Valve Incident</div>
                <div className="text-xs" style={{ color: 'var(--textTertiary)' }}>
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
                <Loader2 className="h-4 w-4 mr-2 animate-spin" style={{ color: 'var(--textPrimary)' }} />
              ) : (
                <Video className="h-4 w-4 mr-2" style={{ color: 'var(--textPrimary)' }} />
              )}
              <div>
                <div className="font-medium" style={{ fontFamily: 'var(--font-nav)' }}>Scenario 2: Oil Rig Analysis</div>
                <div className="text-xs" style={{ color: 'var(--textTertiary)' }}>
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
                <Loader2 className="h-4 w-4 mr-2 animate-spin" style={{ color: 'var(--textSecondary)' }} />
              ) : (
                <Video className="h-4 w-4 mr-2" style={{ color: 'var(--textSecondary)' }} />
              )}
              <div>
                <div className="font-medium" style={{ fontFamily: 'var(--font-nav)' }}>Scenario 3: Water Pipe Leakage</div>
                <div className="text-xs" style={{ color: 'var(--textTertiary)' }}>
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
                <Loader2 className="h-4 w-4 mr-2 animate-spin" style={{ color: 'var(--warning)' }} />
              ) : (
                <Video className="h-4 w-4 mr-2" style={{ color: 'var(--warning)' }} />
              )}
              <div>
                <div className="font-medium" style={{ fontFamily: 'var(--font-nav)' }}>Scenario 4: Data Center Arc Flash</div>
                <div className="text-xs" style={{ color: 'var(--textTertiary)' }}>
                  {scenario4Loading ? "Starting 20s simulation..." : "20s electrical hazard monitoring"}
                </div>
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Mode selector tabs - text only */}
        <div 
          className="hidden md:flex items-center gap-1 rounded-md p-1"
          style={{ border: '1px solid var(--border0)' }}
        >
          {modes.slice(0, 3).map((mode) => {
            const isActive = pathname.startsWith(mode.path)
            return (
              <div
                key={mode.path}
                className={cn(
                  "flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium transition-colors",
                )}
                style={{
                  fontFamily: 'var(--font-nav)',
                  backgroundColor: isActive ? 'var(--trustMuted)' : 'transparent',
                  color: isActive ? 'var(--textPrimary)' : 'var(--textTertiary)',
                }}
              >
                <span className="hidden lg:inline">{mode.label.split(" ")[0]}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Center: Data Ingest Button */}
      <div className="flex items-center">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex items-center gap-2 rounded-md bg-primary/10 border border-primary/20 px-3 py-1.5 hover:bg-primary/20 transition-colors cursor-pointer text-primary"
            >
              <Database className="h-4 w-4" />
              <span className="text-sm font-medium">Data Ingest</span>
              <ChevronDown className="h-3 w-3 opacity-60" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="center" className="w-64">
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Select Data Source
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => handleOpenIngestDialog("sensors")}
              className="cursor-pointer"
            >
              <Gauge className="h-4 w-4 mr-2 text-green-500" />
              <div>
                <div className="font-medium">Live Sensor Feed</div>
                <div className="text-xs text-muted-foreground">Connect directly to sensors</div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => handleOpenIngestDialog("csv")}
              className="cursor-pointer"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2 text-blue-500" />
              <div>
                <div className="font-medium">Import CSV/JSON</div>
                <div className="text-xs text-muted-foreground">Upload telemetry data file</div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => handleOpenIngestDialog("historian")}
              className="cursor-pointer"
            >
              <History className="h-4 w-4 mr-2 text-purple-500" />
              <div>
                <div className="font-medium">Historian Data</div>
                <div className="text-xs text-muted-foreground">Connect to data historian</div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => handleOpenIngestDialog("scada")}
              className="cursor-pointer"
            >
              <Server className="h-4 w-4 mr-2 text-orange-500" />
              <div>
                <div className="font-medium">SCADA System</div>
                <div className="text-xs text-muted-foreground">Import from SCADA/OPC-UA</div>
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Right: Status */}
      <div className="flex items-center gap-4">
        {/* System Status */}
        <div 
          className="hidden sm:flex items-center gap-3 text-xs"
          style={{ fontFamily: 'var(--font-nav)', color: 'var(--textTertiary)' }}
        >
          <div className="flex items-center gap-1.5">
            {systemStatus.connected ? (
              <Wifi className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <WifiOff className="h-3.5 w-3.5" style={{ color: 'var(--critical)' }} />
            )}
            <span>{systemStatus.sources} sources</span>
          </div>
          <span style={{ color: 'var(--border1)' }}>|</span>
          <span>Synced {systemStatus.lastSync}</span>
        </div>
      </div>

      {/* Data Ingest Dialog */}
      <Dialog open={showIngestDialog} onOpenChange={setShowIngestDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              {ingestTypeLabels[ingestType] || "Data Ingest"}
            </DialogTitle>
            <DialogDescription>
              Import telemetry data to begin analysis. For this demo, upload a CSV file to start Scenario 1.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* File Upload Area */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                selectedFile
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50 hover:bg-muted/50"
              )}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.json"
                onChange={handleFileSelect}
                className="hidden"
              />
              {selectedFile ? (
                <div className="space-y-2">
                  <FileSpreadsheet className="h-10 w-10 mx-auto text-primary" />
                  <div className="font-medium">{selectedFile.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                  <div className="text-sm font-medium">Drop your file here or click to browse</div>
                  <div className="text-xs text-muted-foreground">
                    Supports CSV and JSON formats
                  </div>
                </div>
              )}
            </div>

            {/* Info about what will happen */}
            <div className="rounded-md bg-muted p-3 text-sm">
              <div className="font-medium mb-1">What happens next?</div>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• Your data will be ingested into the trust pipeline</li>
                <li>• Scenario 1 (Valve Incident) simulation will start</li>
                <li>• You&apos;ll see real-time trust scoring and decisions</li>
              </ul>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowIngestDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleImportAndRun}
              disabled={!selectedFile || isImporting}
            >
              {isImporting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Import & Run Scenario
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </header>
  )
}
