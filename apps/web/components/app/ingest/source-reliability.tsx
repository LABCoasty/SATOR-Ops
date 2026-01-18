"use client"

import { useMemo } from "react"
import { cn } from "@/lib/utils"
import { CheckCircle, AlertTriangle, XCircle, Clock, Loader2 } from "lucide-react"
import { useDataSources } from "@/hooks/use-telemetry"
import { useOptionalSimulationContext } from "@/contexts/simulation-context"

const StatusIcon = ({ status }: { status: "online" | "degraded" | "offline" }) => {
  switch (status) {
    case "online":
      return <CheckCircle className="h-4 w-4 text-success" />
    case "degraded":
      return <AlertTriangle className="h-4 w-4 text-warning" />
    case "offline":
      return <XCircle className="h-4 w-4 text-destructive" />
  }
}

// Source definitions for simulation
const SOURCE_DEFS = [
  { id: "primary_sensor_array", name: "Primary Sensor Array", type: "sensor", baseReliability: 0.98 },
  { id: "backup_telemetry", name: "Backup Telemetry", type: "sensor", baseReliability: 0.95 },
  { id: "external_feed_alpha", name: "External Feed Alpha", type: "external", baseReliability: 0.87 },
  { id: "external_feed_beta", name: "External Feed Beta", type: "external", baseReliability: 0.72 },
  { id: "legacy_system_link", name: "Legacy System Link", type: "legacy", baseReliability: 0.65 },
  { id: "remote_station_c", name: "Remote Station C", type: "remote", baseReliability: 0.0 },
]

export function SourceReliability() {
  const { sources: apiSources, loading, error } = useDataSources()
  const simulation = useOptionalSimulationContext()

  // Generate simulation sources with dynamic reliability based on time
  const simulationSources = useMemo(() => {
    if (!simulation?.isRunning || !simulation?.state) {
      return []
    }

    const timeSec = simulation.state.current_time_sec
    const trustScore = simulation.state.trust_score

    return SOURCE_DEFS.map(def => {
      // Adjust reliability based on simulation time and events
      let reliability = def.baseReliability
      let status: "online" | "degraded" | "offline" = "online"
      let lastUpdate = "2s ago"

      // Remote Station C goes offline after 30s
      if (def.id === "remote_station_c") {
        if (timeSec > 30) {
          reliability = 0
          status = "offline"
          lastUpdate = "15m ago"
        } else {
          reliability = 0.45 - (timeSec / 100)
          status = reliability > 0.3 ? "degraded" : "offline"
          lastUpdate = "2m ago"
        }
      }
      // External feeds degrade over time
      else if (def.id === "external_feed_beta") {
        reliability = Math.max(0.5, def.baseReliability - (timeSec / 200))
        status = reliability < 0.7 ? "degraded" : "online"
        lastUpdate = `${Math.floor(timeSec / 10) * 10 + 45}s ago`
      }
      else if (def.id === "external_feed_alpha") {
        reliability = Math.max(0.75, def.baseReliability - (timeSec / 300))
        status = reliability < 0.85 ? "degraded" : "online"
        lastUpdate = `${Math.floor(timeSec / 5) * 2 + 12}s ago`
      }
      // Legacy system has intermittent issues
      else if (def.id === "legacy_system_link") {
        reliability = def.baseReliability + Math.sin(timeSec / 10) * 0.05
        status = reliability < 0.65 ? "degraded" : "online"
        lastUpdate = "2m ago"
      }
      // Primary and backup stay relatively stable
      else {
        reliability = Math.max(0.9, def.baseReliability - (timeSec / 1000))
        lastUpdate = `${Math.floor(timeSec % 10)}s ago`
      }

      return {
        id: def.id,
        name: def.name,
        reliability: Math.max(0, Math.min(1, reliability)),
        last_update: lastUpdate,
        status,
        type: def.type
      }
    })
  }, [simulation?.isRunning, simulation?.state])

  // Use simulation data when running, otherwise use API data
  const sources = simulation?.isRunning && simulationSources.length > 0 
    ? simulationSources 
    : apiSources

  if (loading && !simulation?.isRunning) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if ((error) && !simulation?.isRunning) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive text-sm">
        Failed to load sources
      </div>
    )
  }

  // Calculate composite reliability
  const onlineSources = sources.filter(s => s.status !== "offline")
  const compositeReliability = onlineSources.length > 0
    ? onlineSources.reduce((sum, s) => sum + s.reliability, 0) / onlineSources.length
    : 0

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-semibold">Source Reliability</h2>
        <p className="text-xs text-muted-foreground">Trust weighting per data source</p>
      </div>
      <div className="p-4 space-y-3">
        {sources.map((source) => (
          <div key={source.id} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StatusIcon status={source.status} />
                <span className="text-sm font-medium">{source.name}</span>
              </div>
              <span
                className={cn(
                  "text-xs font-mono",
                  source.reliability >= 0.9 && "text-success",
                  source.reliability >= 0.7 && source.reliability < 0.9 && "text-warning",
                  source.reliability < 0.7 && "text-muted-foreground",
                )}
              >
                {source.status === "offline" ? "—" : (source.reliability * 100).toFixed(0) + "%"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-1.5 flex-1 rounded-full bg-muted overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    source.reliability >= 0.9 && "bg-success",
                    source.reliability >= 0.7 && source.reliability < 0.9 && "bg-warning",
                    source.reliability < 0.7 && source.reliability > 0 && "bg-muted-foreground",
                    source.reliability === 0 && "bg-destructive",
                  )}
                  style={{ width: `${source.reliability * 100}%` }}
                />
              </div>
              <div className="flex items-center gap-1 text-[10px] text-muted-foreground min-w-[50px]">
                <Clock className="h-3 w-3" />
                {source.last_update}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="border-t border-border px-4 py-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Composite reliability</span>
          <span className={cn(
            "font-mono font-medium",
            compositeReliability >= 0.8 && "text-success",
            compositeReliability >= 0.6 && compositeReliability < 0.8 && "text-warning",
            compositeReliability < 0.6 && "text-destructive"
          )}>
            {compositeReliability.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  )
}
