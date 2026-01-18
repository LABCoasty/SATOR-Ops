"use client"

import { useMemo } from "react"
import { X, TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle, Clock, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface TelemetryChannel {
  id: string
  name: string
  source: string
  value: number
  unit: string
  trend: "up" | "down" | "stable"
  status: "normal" | "warning" | "critical"
  sparkline: number[]
  summary: string
  min_threshold: number
  max_threshold: number
}

interface TelemetryDetailModalProps {
  channel: TelemetryChannel
  history: number[]
  onClose: () => void
  currentTimeSec?: number
}

export function TelemetryDetailModal({ channel, history, onClose, currentTimeSec = 0 }: TelemetryDetailModalProps) {
  // Calculate statistics
  const stats = useMemo(() => {
    if (history.length === 0) return null
    
    const min = Math.min(...history)
    const max = Math.max(...history)
    const avg = history.reduce((a, b) => a + b, 0) / history.length
    const latest = history[history.length - 1]
    const previous = history.length > 1 ? history[history.length - 2] : latest
    const change = latest - previous
    const changePercent = previous !== 0 ? ((change / previous) * 100) : 0
    
    // Calculate variance
    const variance = history.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / history.length
    const stdDev = Math.sqrt(variance)
    
    return { min, max, avg, latest, change, changePercent, stdDev }
  }, [history])

  // Determine if value is in danger zone
  const isAboveMax = channel.value > channel.max_threshold
  const isBelowMin = channel.value < channel.min_threshold
  const percentOfRange = ((channel.value - channel.min_threshold) / (channel.max_threshold - channel.min_threshold)) * 100

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal Panel - Left Side */}
      <div className="relative z-10 w-full max-w-xl bg-card border-r border-border shadow-xl flex flex-col h-full animate-in slide-in-from-left duration-300">
        {/* Header */}
        <div className={cn(
          "px-6 py-4 border-b border-border",
          channel.status === "critical" && "bg-destructive/10",
          channel.status === "warning" && "bg-warning/10"
        )}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={cn(
                "h-3 w-3 rounded-full",
                channel.status === "normal" && "bg-success",
                channel.status === "warning" && "bg-warning animate-pulse",
                channel.status === "critical" && "bg-destructive animate-pulse"
              )} />
              <div>
                <h2 className="text-lg font-bold">{channel.name}</h2>
                <p className="text-xs text-muted-foreground">{channel.source}</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Current Value */}
        <div className="px-6 py-4 border-b border-border">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Current Value</p>
              <div className="flex items-baseline gap-2">
                <span className={cn(
                  "text-4xl font-bold font-mono",
                  channel.status === "normal" && "text-success",
                  channel.status === "warning" && "text-warning",
                  channel.status === "critical" && "text-destructive"
                )}>
                  {channel.value.toFixed(1)}
                </span>
                <span className="text-lg text-muted-foreground">{channel.unit}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {stats && (
                <div className={cn(
                  "flex items-center gap-1 px-2 py-1 rounded text-sm",
                  stats.change > 0 && "bg-success/10 text-green-500",
                  stats.change < 0 && "bg-destructive/10 text-red-500",
                  stats.change === 0 && "bg-muted text-muted-foreground"
                )}>
                  {stats.change > 0 ? <TrendingUp className="h-4 w-4 text-green-500" /> : 
                   stats.change < 0 ? <TrendingDown className="h-4 w-4 text-red-500" /> : 
                   <Minus className="h-4 w-4" />}
                  <span>{stats.change > 0 ? "+" : ""}{stats.change.toFixed(2)}</span>
                  <span className="text-xs">({stats.changePercent.toFixed(1)}%)</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Large Graph */}
        <div className="px-6 py-4 border-b border-border flex-shrink-0">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium">Historical Trend</p>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>Last {history.length} readings</span>
            </div>
          </div>
          <LargeGraph 
            data={history} 
            trend={channel.trend}
            minThreshold={channel.min_threshold}
            maxThreshold={channel.max_threshold}
            unit={channel.unit}
          />
        </div>

        {/* Statistics */}
        {stats && (
          <div className="px-6 py-4 border-b border-border">
            <p className="text-sm font-medium mb-3">Statistics</p>
            <div className="grid grid-cols-2 gap-4">
              <StatCard label="Minimum" value={stats.min.toFixed(1)} unit={channel.unit} />
              <StatCard label="Maximum" value={stats.max.toFixed(1)} unit={channel.unit} />
              <StatCard label="Average" value={stats.avg.toFixed(1)} unit={channel.unit} />
              <StatCard label="Std Dev" value={stats.stdDev.toFixed(2)} unit={channel.unit} />
            </div>
          </div>
        )}

        {/* Threshold Info */}
        <div className="px-6 py-4 border-b border-border">
          <p className="text-sm font-medium mb-3">Operating Range</p>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Minimum Threshold</span>
              <span className="font-mono">{channel.min_threshold}{channel.unit}</span>
            </div>
            <div className="relative h-3 bg-muted rounded-full overflow-hidden">
              {/* Safe zone */}
              <div className="absolute inset-y-0 bg-success/30" style={{ left: '10%', right: '10%' }} />
              {/* Current position indicator */}
              <div 
                className={cn(
                  "absolute top-0 bottom-0 w-1 -ml-0.5 rounded-full",
                  channel.status === "normal" && "bg-success",
                  channel.status === "warning" && "bg-warning",
                  channel.status === "critical" && "bg-destructive"
                )}
                style={{ left: `${Math.max(0, Math.min(100, percentOfRange))}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Maximum Threshold</span>
              <span className="font-mono">{channel.max_threshold}{channel.unit}</span>
            </div>
          </div>
        </div>

        {/* Status Summary */}
        <div className="px-6 py-4 flex-1 overflow-auto">
          <p className="text-sm font-medium mb-3">Status Analysis</p>
          <div className={cn(
            "rounded-lg p-4",
            channel.status === "normal" && "bg-success/10 border border-success/20",
            channel.status === "warning" && "bg-warning/10 border border-warning/20",
            channel.status === "critical" && "bg-destructive/10 border border-destructive/20"
          )}>
            <div className="flex items-start gap-3">
              {channel.status === "normal" ? (
                <CheckCircle className="h-5 w-5 text-success mt-0.5" />
              ) : (
                <AlertTriangle className={cn(
                  "h-5 w-5 mt-0.5",
                  channel.status === "warning" && "text-warning",
                  channel.status === "critical" && "text-destructive"
                )} />
              )}
              <div>
                <p className={cn(
                  "font-medium",
                  channel.status === "normal" && "text-success",
                  channel.status === "warning" && "text-warning",
                  channel.status === "critical" && "text-destructive"
                )}>
                  {channel.status === "normal" && "Operating Normally"}
                  {channel.status === "warning" && "Warning: Attention Required"}
                  {channel.status === "critical" && "Critical: Immediate Action Needed"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">{channel.summary}</p>
                
                {channel.status !== "normal" && (
                  <div className="mt-3 space-y-1 text-sm">
                    <p className="text-muted-foreground">Recommendations:</p>
                    <ul className="list-disc list-inside text-muted-foreground space-y-1">
                      {channel.status === "warning" && (
                        <>
                          <li>Monitor for further changes</li>
                          <li>Check related sensors for correlation</li>
                          <li>Review recent operational changes</li>
                        </>
                      )}
                      {channel.status === "critical" && (
                        <>
                          <li>Verify reading with backup sensors</li>
                          <li>Consider initiating safety protocols</li>
                          <li>Alert on-site personnel immediately</li>
                          <li>Document incident for audit trail</li>
                        </>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border bg-muted/30">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Activity className="h-3 w-3" />
              <span>Simulation time: {currentTimeSec.toFixed(0)}s</span>
            </div>
            <span>Channel ID: {channel.id}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="rounded-md bg-muted/50 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-mono font-medium">
        {value}<span className="text-xs text-muted-foreground ml-1">{unit}</span>
      </p>
    </div>
  )
}

function LargeGraph({ 
  data, 
  trend, 
  minThreshold, 
  maxThreshold,
  unit
}: { 
  data: number[]
  trend: "up" | "down" | "stable"
  minThreshold: number
  maxThreshold: number
  unit: string
}) {
  const height = 180
  const width = 460
  const padding = { top: 20, right: 50, bottom: 30, left: 10 }
  
  const graphWidth = width - padding.left - padding.right
  const graphHeight = height - padding.top - padding.bottom

  // Calculate min/max for scaling (include thresholds)
  const allValues = [...data, minThreshold, maxThreshold]
  const dataMin = Math.min(...allValues) - (maxThreshold - minThreshold) * 0.1
  const dataMax = Math.max(...allValues) + (maxThreshold - minThreshold) * 0.1
  const range = dataMax - dataMin || 1

  // Generate path points
  const points = data.map((v, i) => {
    const x = padding.left + (i / Math.max(1, data.length - 1)) * graphWidth
    const y = padding.top + graphHeight - ((v - dataMin) / range) * graphHeight
    return { x, y, value: v }
  })

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`).join(' ')

  // Threshold lines
  const minThresholdY = padding.top + graphHeight - ((minThreshold - dataMin) / range) * graphHeight
  const maxThresholdY = padding.top + graphHeight - ((maxThreshold - dataMin) / range) * graphHeight

  // Color based on trend direction: green for up, red for down, yellow/orange for stable
  const strokeColor =
    trend === "up" ? "#22c55e" : // green-500
    trend === "down" ? "#ef4444" : // red-500
    "#f97316" // orange-500 for stable/static

  // Y-axis labels
  const yLabels = [dataMax, (dataMax + dataMin) / 2, dataMin].map(v => ({
    value: v.toFixed(1),
    y: padding.top + graphHeight - ((v - dataMin) / range) * graphHeight
  }))

  return (
    <svg width={width} height={height} className="overflow-visible">
      {/* Grid lines */}
      {yLabels.map((label, i) => (
        <g key={i}>
          <line
            x1={padding.left}
            x2={padding.left + graphWidth}
            y1={label.y}
            y2={label.y}
            stroke="var(--border)"
            strokeDasharray="4,4"
            strokeWidth="1"
          />
          <text
            x={padding.left + graphWidth + 5}
            y={label.y + 4}
            className="text-[10px] fill-muted-foreground"
          >
            {label.value}
          </text>
        </g>
      ))}

      {/* Threshold zone (safe area) */}
      <rect
        x={padding.left}
        y={maxThresholdY}
        width={graphWidth}
        height={minThresholdY - maxThresholdY}
        fill="var(--success)"
        opacity={0.1}
      />

      {/* Min threshold line */}
      <line
        x1={padding.left}
        x2={padding.left + graphWidth}
        y1={minThresholdY}
        y2={minThresholdY}
        stroke="var(--success)"
        strokeWidth="1"
        strokeDasharray="6,3"
        opacity={0.5}
      />
      <text
        x={padding.left + graphWidth + 5}
        y={minThresholdY + 4}
        className="text-[9px] fill-success"
      >
        Min
      </text>

      {/* Max threshold line */}
      <line
        x1={padding.left}
        x2={padding.left + graphWidth}
        y1={maxThresholdY}
        y2={maxThresholdY}
        stroke="var(--destructive)"
        strokeWidth="1"
        strokeDasharray="6,3"
        opacity={0.5}
      />
      <text
        x={padding.left + graphWidth + 5}
        y={maxThresholdY + 4}
        className="text-[9px] fill-destructive"
      >
        Max
      </text>

      {/* Area under curve */}
      {points.length > 1 && (
        <path
          d={`${pathD} L ${points[points.length - 1].x},${padding.top + graphHeight} L ${points[0].x},${padding.top + graphHeight} Z`}
          fill={strokeColor}
          opacity={0.1}
        />
      )}

      {/* Main line */}
      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Data points */}
      {points.map((p, i) => (
        <circle
          key={i}
          cx={p.x}
          cy={p.y}
          r={i === points.length - 1 ? 5 : 2}
          fill={i === points.length - 1 ? strokeColor : "var(--card)"}
          stroke={strokeColor}
          strokeWidth={i === points.length - 1 ? 2 : 1}
        />
      ))}

      {/* Latest value label */}
      {points.length > 0 && (
        <g>
          <rect
            x={points[points.length - 1].x - 25}
            y={points[points.length - 1].y - 28}
            width={50}
            height={20}
            rx={4}
            fill="var(--card)"
            stroke={strokeColor}
            strokeWidth="1"
          />
          <text
            x={points[points.length - 1].x}
            y={points[points.length - 1].y - 14}
            textAnchor="middle"
            className="text-[11px] font-mono font-medium fill-foreground"
          >
            {points[points.length - 1].value.toFixed(1)}{unit}
          </text>
        </g>
      )}

      {/* X-axis time labels */}
      <text
        x={padding.left}
        y={height - 5}
        className="text-[10px] fill-muted-foreground"
      >
        Oldest
      </text>
      <text
        x={padding.left + graphWidth}
        y={height - 5}
        textAnchor="end"
        className="text-[10px] fill-muted-foreground"
      >
        Latest
      </text>
    </svg>
  )
}
