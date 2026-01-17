"use client"

import { AlertTriangle, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface Contradiction {
  id: string
  sources: [string, string]
  values: [string, string]
  severity: "low" | "medium" | "high"
  resolution: string
}

const contradictions: Contradiction[] = [
  {
    id: "c1",
    sources: ["Flow Sensor A", "Flow Sensor B"],
    values: ["234 L/min", "248 L/min"],
    severity: "medium",
    resolution: "Using weighted average (0.87/0.72). Sensor B calibration pending.",
  },
  {
    id: "c2",
    sources: ["External Feed Alpha", "External Feed Beta"],
    values: ["Clear conditions", "Light precipitation"],
    severity: "low",
    resolution: "Feed Beta update delayed. Using Alpha (higher reliability).",
  },
]

const severityColors = {
  low: "border-muted text-muted-foreground",
  medium: "border-warning text-warning",
  high: "border-destructive text-destructive",
}

export function ContradictionsPanel() {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-warning" />
            <h2 className="font-semibold">Detected Contradictions</h2>
          </div>
          <span className="rounded-md bg-warning/20 px-2 py-0.5 text-xs font-medium text-warning">
            {contradictions.length} active
          </span>
        </div>
      </div>

      <div className="divide-y divide-border">
        {contradictions.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-muted-foreground">
            No contradictions detected at this time.
          </div>
        ) : (
          contradictions.map((c) => (
            <div key={c.id} className="px-4 py-3 space-y-3">
              {/* Contradiction display */}
              <div className="flex items-center gap-3">
                <div className={cn("rounded-md border px-3 py-2 text-center flex-1", severityColors[c.severity])}>
                  <p className="text-xs opacity-70">{c.sources[0]}</p>
                  <p className="font-mono text-sm font-medium">{c.values[0]}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                <div className={cn("rounded-md border px-3 py-2 text-center flex-1", severityColors[c.severity])}>
                  <p className="text-xs opacity-70">{c.sources[1]}</p>
                  <p className="font-mono text-sm font-medium">{c.values[1]}</p>
                </div>
              </div>

              {/* Resolution */}
              <div className="rounded-md bg-muted/50 px-3 py-2">
                <span className="text-xs font-medium text-muted-foreground">Resolution: </span>
                <span className="text-xs text-muted-foreground">{c.resolution}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
