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

  // Generate simulation sources with dynamic reliability based on time and scenario
  const simulationSources = useMemo(() => {
    if (!simulation?.isRunning || !simulation?.state) {
      return []
    }

    const timeSec = simulation.state.current_time_sec
    const activeScenario = simulation.activeScenario
    
    // Check if this is a vision scenario with video shown (after 5 seconds)
    const isVisionScenario = activeScenario === "scenario2" || activeScenario === "scenario3" || activeScenario === "scenario4"
    const isScenario4 = activeScenario === "scenario4"
    const videoShown = timeSec >= 5
    
    // Degradation factor: 0 before video, then ramps up to 1 over remaining 15 seconds
    const degradationFactor = videoShown ? Math.min(1, (timeSec - 5) / 15) : 0

    return SOURCE_DEFS.map(def => {
      let reliability = def.baseReliability
      let status: "online" | "degraded" | "offline" = "online"
      let lastUpdate = "2s ago"

      if (isVisionScenario && videoShown) {
        // For Scenario 4 (Data Center), all sources degrade much more dramatically
        if (isScenario4) {
          if (def.id === "primary_sensor_array") {
            // Primary sensors start failing due to electrical interference
            reliability = def.baseReliability - (degradationFactor * 0.4) + Math.sin(timeSec * 2) * 0.1
            status = reliability < 0.7 ? "degraded" : reliability < 0.5 ? "offline" : "online"
            lastUpdate = reliability < 0.8 ? `${Math.floor(degradationFactor * 30) + 5}s ago` : "2s ago"
          }
          else if (def.id === "backup_telemetry") {
            // Backup telemetry also affected by arc flash conditions
            reliability = def.baseReliability - (degradationFactor * 0.35)
            status = reliability < 0.75 ? "degraded" : "online"
            lastUpdate = `${Math.floor(degradationFactor * 20) + 3}s ago`
          }
          else if (def.id === "external_feed_alpha") {
            // External feeds lose connection
            reliability = def.baseReliability - (degradationFactor * 0.5)
            status = reliability < 0.6 ? "degraded" : reliability < 0.4 ? "offline" : "online"
            lastUpdate = `${Math.floor(degradationFactor * 45) + 10}s ago`
          }
          else if (def.id === "external_feed_beta") {
            // Goes offline quickly
            reliability = Math.max(0, def.baseReliability - (degradationFactor * 0.7))
            status = reliability < 0.5 ? "offline" : reliability < 0.65 ? "degraded" : "online"
            lastUpdate = reliability < 0.5 ? "2m ago" : `${Math.floor(degradationFactor * 60)}s ago`
          }
          else if (def.id === "legacy_system_link") {
            // Legacy system completely fails
            reliability = Math.max(0, def.baseReliability - (degradationFactor * 0.65))
            status = reliability < 0.3 ? "offline" : reliability < 0.5 ? "degraded" : "online"
            lastUpdate = reliability < 0.3 ? "5m ago" : "1m ago"
          }
          else if (def.id === "remote_station_c") {
            // Already offline, stays offline
            reliability = 0
            status = "offline"
            lastUpdate = "15m ago"
          }
        } else {
          // Normal vision scenario degradation (scenario 2 & 3)
          if (def.id === "remote_station_c") {
            reliability = Math.max(0, 0.45 - (degradationFactor * 0.5))
            status = reliability <= 0 ? "offline" : "degraded"
            lastUpdate = reliability <= 0 ? "15m ago" : "2m ago"
          }
          else if (def.id === "external_feed_beta") {
            reliability = Math.max(0.4, def.baseReliability - (degradationFactor * 0.3))
            status = reliability < 0.6 ? "degraded" : "online"
            lastUpdate = `${Math.floor(degradationFactor * 40) + 10}s ago`
          }
          else if (def.id === "external_feed_alpha") {
            reliability = Math.max(0.6, def.baseReliability - (degradationFactor * 0.2))
            status = reliability < 0.8 ? "degraded" : "online"
            lastUpdate = `${Math.floor(degradationFactor * 20) + 5}s ago`
          }
          else if (def.id === "legacy_system_link") {
            reliability = def.baseReliability - (degradationFactor * 0.2) + Math.sin(timeSec) * 0.05
            status = reliability < 0.55 ? "degraded" : "online"
            lastUpdate = "1m ago"
          }
          else {
            // Primary and backup degrade slightly
            reliability = def.baseReliability - (degradationFactor * 0.1)
            lastUpdate = `${Math.floor(timeSec % 5)}s ago`
          }
        }
      } else {
        // Before video shows - stable baseline
        if (def.id === "remote_station_c") {
          reliability = 0.45
          status = "degraded"
          lastUpdate = "2m ago"
        }
        else if (def.id === "external_feed_beta") {
          reliability = def.baseReliability
          status = reliability < 0.75 ? "degraded" : "online"
          lastUpdate = "30s ago"
        }
        else {
          lastUpdate = `${Math.floor(timeSec % 10)}s ago`
        }
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
  }, [simulation?.isRunning, simulation?.state, simulation?.activeScenario])

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
