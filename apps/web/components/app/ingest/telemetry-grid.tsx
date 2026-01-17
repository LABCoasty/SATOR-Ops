"use client"

import { useState } from "react"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"

interface TelemetryChannel {
  id: string
  name: string
  value: number
  unit: string
  trend: "up" | "down" | "stable"
  status: "normal" | "warning" | "critical"
  sparkline: number[]
  summary: string
}

const channels: TelemetryChannel[] = [
  {
    id: "temp_01",
    name: "Core Temperature",
    value: 72.4,
    unit: "°C",
    trend: "up",
    status: "normal",
    sparkline: [68, 69, 70, 71, 70, 72, 72.4],
    summary: "Operating within normal parameters. Slight upward trend over the last hour.",
  },
  {
    id: "pressure_01",
    name: "System Pressure",
    value: 14.7,
    unit: "PSI",
    trend: "stable",
    status: "normal",
    sparkline: [14.6, 14.7, 14.7, 14.8, 14.7, 14.7, 14.7],
    summary: "Stable pressure reading. No anomalies detected.",
  },
  {
    id: "flow_01",
    name: "Flow Rate A",
    value: 234,
    unit: "L/min",
    trend: "down",
    status: "warning",
    sparkline: [250, 248, 245, 240, 238, 236, 234],
    summary: "Declining flow rate detected. May indicate partial blockage or pump degradation.",
  },
  {
    id: "vibration_01",
    name: "Vibration Sensor",
    value: 0.42,
    unit: "mm/s",
    trend: "up",
    status: "warning",
    sparkline: [0.35, 0.36, 0.38, 0.39, 0.4, 0.41, 0.42],
    summary: "Vibration levels increasing. Approaching upper threshold.",
  },
  {
    id: "power_01",
    name: "Power Draw",
    value: 847,
    unit: "kW",
    trend: "stable",
    status: "normal",
    sparkline: [845, 846, 848, 847, 846, 847, 847],
    summary: "Consistent power consumption. Operating efficiently.",
  },
  {
    id: "humidity_01",
    name: "Ambient Humidity",
    value: 45,
    unit: "%",
    trend: "down",
    status: "normal",
    sparkline: [52, 50, 48, 47, 46, 45, 45],
    summary: "Humidity decreasing. Within acceptable range for operations.",
  },
]

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
  const [expanded, setExpanded] = useState<string | null>(null)

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-semibold">Live Telemetry Channels</h2>
        <p className="text-xs text-muted-foreground">Real-time data streams with plain-language summaries</p>
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
                </div>
                <div className="flex items-center gap-4">
                  <Sparkline data={channel.sparkline} status={channel.status} />
                  <div className="flex items-center gap-2 min-w-[80px] justify-end">
                    <span className="font-mono text-sm font-medium">
                      {channel.value}
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
              <div className="mt-3 ml-5 rounded-md bg-muted/50 p-3">
                <p className="text-sm text-muted-foreground leading-relaxed">{channel.summary}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
