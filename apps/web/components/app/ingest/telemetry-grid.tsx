"use client"

import { useState, useEffect, useMemo } from "react"
import { TrendingUp, TrendingDown, Minus, Loader2, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTelemetry, type TelemetryChannel } from "@/hooks/use-telemetry"
import { useOptionalSimulationContext } from "@/contexts/simulation-context"
import { TelemetryDetailModal } from "./telemetry-detail-modal"

const TrendIcon = ({ trend }: { trend: "up" | "down" | "stable" }) => {
  switch (trend) {
    case "up":
      return <TrendingUp className="h-3 w-3 text-green-500" />
    case "down":
      return <TrendingDown className="h-3 w-3 text-red-500" />
    default:
      return <Minus className="h-3 w-3 text-orange-500" />
  }
}

const Sparkline = ({ data, trend }: { data: number[]; trend: "up" | "down" | "stable" }) => {
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const height = 24
  const width = 60

  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * width
      const y = height - ((v - min) / range) * height
      return `${x},${y}`
    })
    .join(" ")

  // Color based on trend direction: green for up, red for down, yellow/orange for stable
  const strokeColor =
    trend === "up" ? "#22c55e" : // green-500
    trend === "down" ? "#ef4444" : // red-500
    "#f97316" // orange-500 for stable/static

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

// Channel definitions for simulation data mapping
const CHANNEL_DEFS = [
  { id: "core_temp", name: "Core Temperature", source: "primary_sensor_array", unit: "°C", min: 60, max: 85 },
  { id: "pressure", name: "System Pressure", source: "primary_sensor_array", unit: "PSI", min: 10, max: 20 },
  { id: "flow_a", name: "Flow Rate A", source: "external_feed_alpha", unit: "L/min", min: 200, max: 300 },
  { id: "flow_b", name: "Flow Rate B", source: "external_feed_beta", unit: "L/min", min: 200, max: 300 },
  { id: "vibration", name: "Vibration Sensor", source: "backup_telemetry", unit: "mm/s", min: 0, max: 1 },
  { id: "power", name: "Power Draw", source: "primary_sensor_array", unit: "kW", min: 800, max: 900 },
  { id: "humidity", name: "Ambient Humidity", source: "backup_telemetry", unit: "%", min: 30, max: 60 },
]

interface TelemetryGridProps {
  compact?: boolean
}

export function TelemetryGrid({ compact = false }: TelemetryGridProps) {
  const { channels: apiChannels, loading, error } = useTelemetry()
  const simulation = useOptionalSimulationContext()
  const [selectedChannel, setSelectedChannel] = useState<TelemetryChannel | null>(null)

  // Track full history for each channel (more data points for the detail modal)
  const [fullHistory, setFullHistory] = useState<Record<string, number[]>>({})

  // Track sparkline history for simulation data (last 10 points for inline display)
  const [sparklineHistory, setSparklineHistory] = useState<Record<string, number[]>>({})

  // Update history when simulation telemetry changes
  useEffect(() => {
    if (simulation?.isRunning && simulation?.telemetry?.channels) {
      // Update full history (keep up to 50 points)
      setFullHistory(prev => {
        const newHistory = { ...prev }
        Object.entries(simulation.telemetry!.channels).forEach(([key, data]) => {
          const value = (data as { value: number }).value
          const history = prev[key] || []
          newHistory[key] = [...history.slice(-49), value]
        })
        return newHistory
      })

      // Update sparkline history (keep last 10 for inline display)
      setSparklineHistory(prev => {
        const newHistory = { ...prev }
        Object.entries(simulation.telemetry!.channels).forEach(([key, data]) => {
          const value = (data as { value: number }).value
          const history = prev[key] || []
          newHistory[key] = [...history.slice(-9), value]
        })
        return newHistory
      })
    }
  }, [simulation?.isRunning, simulation?.telemetry])

  // Reset history when simulation stops
  useEffect(() => {
    if (!simulation?.isRunning) {
      setFullHistory({})
      setSparklineHistory({})
    }
  }, [simulation?.isRunning])

  // Convert simulation telemetry to channel format
  const simulationChannels: TelemetryChannel[] = useMemo(() => {
    if (!simulation?.isRunning || !simulation?.telemetry?.channels) {
      return []
    }

    return CHANNEL_DEFS.map(def => {
      const data = simulation.telemetry!.channels[def.id] as { value: number; unit: string; status: string } | undefined
      if (!data) return null

      const history = sparklineHistory[def.id] || [data.value]
      const prevValue = history.length > 1 ? history[history.length - 2] : data.value
      const trend: "up" | "down" | "stable" =
        data.value > prevValue + 0.5 ? "up" :
          data.value < prevValue - 0.5 ? "down" : "stable"

      return {
        id: def.id,
        name: def.name,
        source: def.source,
        value: data.value,
        unit: def.unit,
        trend,
        status: data.status as "normal" | "warning" | "critical",
        sparkline: history.length >= 2 ? history : [data.value, data.value],
        summary: getSummary(def.id, data.value, data.status),
        min_threshold: def.min,
        max_threshold: def.max,
        timestamp: new Date().toISOString()
      }
    }).filter(Boolean) as TelemetryChannel[]
  }, [simulation?.isRunning, simulation?.telemetry, sparklineHistory])

  // Use simulation data when running, otherwise use API data
  const channels = simulation?.isRunning && simulationChannels.length > 0
    ? simulationChannels
    : apiChannels

  // Handle channel click
  const handleChannelClick = (channel: TelemetryChannel) => {
    setSelectedChannel(channel)
  }

  if (loading && !simulation?.isRunning) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading telemetry...</span>
      </div>
    )
  }

  if (error && !simulation?.isRunning) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-8 flex items-center justify-center">
        <WifiOff className="h-6 w-6 text-destructive" />
        <span className="ml-2 text-destructive">Failed to connect: {error}</span>
      </div>
    )
  }

  // Compact mode: show fewer channels and simpler layout
  const displayChannels = compact ? channels.slice(0, 4) : channels

  return (
    <div className="rounded-lg border border-border bg-card transition-all duration-500 ease-in-out">
      {/* Header - adjusts for compact mode */}
      <div className={cn(
        "border-b border-border transition-all duration-500 ease-in-out",
        compact ? "px-3 py-2" : "px-4 py-3"
      )}>
        <div className="flex items-center justify-between">
          <div className="overflow-hidden">
            <h2 className={cn(
              "font-semibold transition-all duration-300",
              compact ? "text-sm" : "text-base"
            )}>
              {compact ? "Telemetry" : "Live Telemetry Channels"}
            </h2>
            {!compact && (
              <p className="text-xs text-muted-foreground">
                Real-time data streams with plain-language summaries
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className={cn(
              "h-2 w-2 rounded-full animate-pulse",
              simulation?.isRunning ? "bg-primary" : "bg-success"
            )} />
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {displayChannels.length}
              {!compact && " channels"}
              {simulation?.isRunning && !compact && " (LIVE SIM)"}
            </span>
          </div>
        </div>
      </div>

      {/* Channel list */}
      <div className={cn(
        "divide-y divide-border",
        compact && "max-h-[400px] overflow-y-auto"
      )}>
        {displayChannels.map((channel) => (
          <div 
            key={channel.id} 
            className={cn(
              "transition-all duration-300",
              compact ? "px-3 py-2" : "px-4 py-3"
            )}
          >
            <button
              onClick={() => handleChannelClick(channel)}
              className="w-full text-left"
            >
              {compact ? (
                // Compact layout: stacked rows
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      <div
                        className={cn(
                          "h-2 w-2 rounded-full flex-shrink-0",
                          channel.status === "normal" && "bg-success",
                          channel.status === "warning" && "bg-warning",
                          channel.status === "critical" && "bg-destructive",
                        )}
                      />
                      <span className="text-xs font-medium truncate">{channel.name}</span>
                    </div>
                    <span
                      className={cn(
                        "text-muted-foreground flex-shrink-0",
                        channel.trend === "up" && channel.status === "warning" && "text-warning",
                        channel.trend === "down" && channel.status === "warning" && "text-warning",
                      )}
                    >
                      <TrendIcon trend={channel.trend} />
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <Sparkline data={channel.sparkline} trend={channel.trend} />
                    <span className="font-mono text-xs font-medium whitespace-nowrap">
                      {typeof channel.value === 'number' ? channel.value.toFixed(1) : channel.value}
                      <span className="text-muted-foreground ml-0.5">{channel.unit}</span>
                    </span>
                  </div>
                </div>
              ) : (
                // Full layout: horizontal row
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "h-2 w-2 rounded-full",
                        channel.status === "normal" && "bg-success",
                        channel.status === "warning" && "bg-warning",
                        channel.status === "critical" && "bg-destructive",
                      )}
                    />
                    <span className="text-sm font-medium">{channel.name}</span>
                    <span className="text-xs text-muted-foreground">({channel.source})</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <Sparkline data={channel.sparkline} trend={channel.trend} />
                    <div className="flex items-center gap-2 min-w-[80px] justify-end">
                      <span className="font-mono text-sm font-medium">
                        {typeof channel.value === 'number' ? channel.value.toFixed(1) : channel.value}
                        <span className="text-muted-foreground ml-0.5">{channel.unit}</span>
                      </span>
                      <TrendIcon trend={channel.trend} />
                    </div>
                  </div>
                </div>
              )}
            </button>
          </div>
        ))}
      </div>

      {/* More channels indicator for compact mode */}
      {compact && channels.length > displayChannels.length && (
        <div className="border-t border-border px-3 py-2 text-center">
          <span className="text-xs text-muted-foreground">
            +{channels.length - displayChannels.length} more channels
          </span>
        </div>
      )}

      {/* Detail Modal */}
      {selectedChannel && (
        <TelemetryDetailModal
          channel={selectedChannel}
          history={fullHistory[selectedChannel.id] || selectedChannel.sparkline}
          onClose={() => setSelectedChannel(null)}
        />
      )}
    </div>
  )
}

function getSummary(channelId: string, value: number, status: string): string {
  const summaries: Record<string, Record<string, string>> = {
    core_temp: {
      normal: "Temperature within normal operating range.",
      warning: `Temperature elevated at ${value.toFixed(1)}°C. Monitor for further increases.`,
      critical: `CRITICAL: Temperature at ${value.toFixed(1)}°C exceeds safe limits!`
    },
    pressure: {
      normal: "System pressure stable.",
      warning: "Pressure showing slight deviation from baseline.",
      critical: "CRITICAL: Pressure anomaly detected!"
    },
    flow_a: {
      normal: "Flow rate within expected parameters.",
      warning: `Flow rate at ${value.toFixed(1)} L/min showing deviation from expected values.`,
      critical: "CRITICAL: Significant flow rate deviation detected!"
    },
    flow_b: {
      normal: "Secondary flow sensor showing slightly higher values than primary.",
      warning: `Flow rate B at ${value.toFixed(1)} L/min diverging from Flow A.`,
      critical: "CRITICAL: Major divergence between flow sensors!"
    },
    vibration: {
      normal: "Vibration levels nominal.",
      warning: "Slight vibration increase detected.",
      critical: "CRITICAL: Excessive vibration detected!"
    },
    power: {
      normal: "Power consumption within expected range.",
      warning: "Power draw showing fluctuation.",
      critical: "CRITICAL: Abnormal power consumption!"
    },
    humidity: {
      normal: "Ambient humidity stable.",
      warning: "Humidity levels changing.",
      critical: "CRITICAL: Humidity outside acceptable range!"
    }
  }

  return summaries[channelId]?.[status] || "Monitoring channel status."
}
