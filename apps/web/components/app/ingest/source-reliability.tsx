"use client"

import { cn } from "@/lib/utils"
import { CheckCircle, AlertTriangle, XCircle, Clock, Loader2 } from "lucide-react"
import { useDataSources } from "@/hooks/use-telemetry"

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
  const { sources, loading, error } = useDataSources()

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
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
          <span className="font-mono font-medium text-primary">{compositeReliability.toFixed(2)}</span>
        </div>
      </div>
    </div>
  )
}
