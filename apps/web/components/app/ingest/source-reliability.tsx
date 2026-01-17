"use client"

import { cn } from "@/lib/utils"
import { CheckCircle, AlertTriangle, XCircle, Clock } from "lucide-react"

interface Source {
  id: string
  name: string
  reliability: number
  lastUpdate: string
  status: "online" | "degraded" | "offline"
}

const sources: Source[] = [
  { id: "s1", name: "Primary Sensor Array", reliability: 0.98, lastUpdate: "2s ago", status: "online" },
  { id: "s2", name: "Backup Telemetry", reliability: 0.95, lastUpdate: "5s ago", status: "online" },
  { id: "s3", name: "External Feed Alpha", reliability: 0.87, lastUpdate: "12s ago", status: "online" },
  { id: "s4", name: "External Feed Beta", reliability: 0.72, lastUpdate: "45s ago", status: "degraded" },
  { id: "s5", name: "Legacy System Link", reliability: 0.65, lastUpdate: "2m ago", status: "degraded" },
  { id: "s6", name: "Remote Station C", reliability: 0, lastUpdate: "15m ago", status: "offline" },
]

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

export function SourceReliability() {
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
                    "h-full rounded-full transition-all",
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
                {source.lastUpdate}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="border-t border-border px-4 py-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Composite reliability</span>
          <span className="font-mono font-medium text-primary">0.86</span>
        </div>
      </div>
    </div>
  )
}
