"use client"

import { Scale, AlertCircle, FileCheck, Clock } from "lucide-react"

interface EvidenceItem {
  source: string
  value: string
  weight: number
  timestamp: string
}

const evidence: EvidenceItem[] = [
  { source: "Primary Sensor Array", value: "Temperature: 72.4°C", weight: 0.98, timestamp: "14:40:58" },
  { source: "Backup Telemetry", value: "Temperature: 72.1°C", weight: 0.95, timestamp: "14:40:55" },
  { source: "External Feed Alpha", value: "Pressure: 14.7 PSI", weight: 0.87, timestamp: "14:40:52" },
  { source: "Power Monitor", value: "Draw: 847 kW", weight: 0.92, timestamp: "14:40:59" },
  { source: "Vibration Sensor", value: "Level: 0.42 mm/s", weight: 0.89, timestamp: "14:40:57" },
]

export function DecisionContext() {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold">Decision Context</h2>
            <p className="text-xs text-muted-foreground">Evidence supporting the current assessment</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            Last updated: 14:41:00
          </div>
        </div>
      </div>

      {/* Current Assessment */}
      <div className="border-b border-border px-4 py-4">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-success/20">
            <FileCheck className="h-5 w-5 text-success" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium">System Operating Within Normal Parameters</h3>
            <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
              Based on 5 corroborating evidence sources, system health is confirmed stable. Minor vibration elevation
              noted but within acceptable threshold. No immediate action required.
            </p>
          </div>
        </div>
      </div>

      {/* Evidence List */}
      <div className="px-4 py-3">
        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
          <Scale className="h-4 w-4 text-muted-foreground" />
          Supporting Evidence
        </h4>
        <div className="space-y-2">
          {evidence.map((item, i) => (
            <div key={i} className="flex items-center justify-between rounded-md bg-muted/30 px-3 py-2">
              <div className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground font-mono">{item.timestamp}</span>
                <div>
                  <span className="text-sm font-medium">{item.source}</span>
                  <p className="text-xs text-muted-foreground">{item.value}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Weight:</span>
                <span className="font-mono text-sm text-primary">{item.weight.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Known Unknowns */}
      <div className="border-t border-border px-4 py-3">
        <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-warning" />
          Known Unknowns
        </h4>
        <ul className="space-y-1 text-sm text-muted-foreground">
          <li className="flex items-center gap-2">
            <span className="h-1 w-1 rounded-full bg-warning" />
            Remote Station C offline — cannot verify external conditions
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1 w-1 rounded-full bg-warning" />
            Legacy System Link degraded — historical comparison limited
          </li>
        </ul>
      </div>
    </div>
  )
}
