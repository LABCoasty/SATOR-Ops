"use client"

import { useState, useEffect } from "react"
import { TrendingUp, TrendingDown, Minus, Loader2, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTelemetry, type TelemetryChannel } from "@/hooks/use-telemetry"

const TrendIcon = ({ trend }: { trend: "up" | "down" | "stable" }) => {
  switch (trend) {
    case "up":
      return <TrendingUp className="h-3 w-3" />
    case "down":
      return <TrendingDown className="h-3 w-3" />
    default:
      return <Minus className="h-3 w-3" />
  }
}

const Sparkline = ({ data, status }: { data: number[]; status: string }) => {
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

  const strokeColor =
    status === "warning" ? "var(--warning)" : status === "critical" ? "var(--destructive)" : "var(--primary)"

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

export function TelemetryGrid() {
  const { channels, loading, error } = useTelemetry()
  const [expanded, setExpanded] = useState<string | null>(null)

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading telemetry...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-8 flex items-center justify-center">
        <WifiOff className="h-6 w-6 text-destructive" />
        <span className="ml-2 text-destructive">Failed to connect: {error}</span>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold">Live Telemetry Channels</h2>
            <p className="text-xs text-muted-foreground">Real-time data streams with plain-language summaries</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs text-muted-foreground">{channels.length} channels</span>
          </div>
        </div>
      </div>
      <div className="divide-y divide-border">
        {channels.map((channel) => (
          <div key={channel.id} className="px-4 py-3">
            <button
              onClick={() => setExpanded(expanded === channel.id ? null : channel.id)}
              className="w-full text-left"
            >
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
                  <Sparkline data={channel.sparkline} status={channel.status} />
                  <div className="flex items-center gap-2 min-w-[80px] justify-end">
                    <span className="font-mono text-sm font-medium">
                      {typeof channel.value === 'number' ? channel.value.toFixed(1) : channel.value}
                      <span className="text-muted-foreground ml-0.5">{channel.unit}</span>
                    </span>
                    <span
                      className={cn(
                        "text-muted-foreground",
                        channel.trend === "up" && channel.status === "warning" && "text-warning",
                        channel.trend === "down" && channel.status === "warning" && "text-warning",
                      )}
                    >
                      <TrendIcon trend={channel.trend} />
                    </span>
                  </div>
                </div>
              </div>
            </button>
            {expanded === channel.id && (
              <div className="mt-3 ml-5 rounded-md bg-muted/50 p-3 space-y-2">
                <p className="text-sm text-muted-foreground leading-relaxed">{channel.summary}</p>
                <div className="flex gap-4 text-xs text-muted-foreground">
                  <span>Min: {channel.min_threshold}{channel.unit}</span>
                  <span>Max: {channel.max_threshold}{channel.unit}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
