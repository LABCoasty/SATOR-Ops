"use client"

import { Database, ExternalLink } from "lucide-react"

interface TelemetryRef {
  source: string
  reading: string
  timestamp: string
  hash: string
}

const references: TelemetryRef[] = [
  { source: "Primary Sensor Array", reading: "Temp: 72.4°C", timestamp: "14:40:58.234", hash: "0x7a3f...b2c1" },
  { source: "Backup Telemetry", reading: "Temp: 72.1°C", timestamp: "14:40:55.891", hash: "0x8b4e...c3d2" },
  { source: "Flow Sensor A", reading: "234 L/min", timestamp: "14:40:57.445", hash: "0x9c5f...d4e3" },
  { source: "Flow Sensor B", reading: "248 L/min", timestamp: "14:40:56.123", hash: "0xad6g...e5f4" },
  { source: "Power Monitor", reading: "847 kW", timestamp: "14:40:59.012", hash: "0xbe7h...f6g5" },
  { source: "Vibration Sensor", reading: "0.42 mm/s", timestamp: "14:40:57.789", hash: "0xcf8i...g7h6" },
]

export function TelemetryReferences() {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold">Telemetry References</h2>
          </div>
          <span className="text-xs text-muted-foreground">{references.length} data points</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="px-4 py-2 text-left font-medium text-muted-foreground">Source</th>
              <th className="px-4 py-2 text-left font-medium text-muted-foreground">Reading</th>
              <th className="px-4 py-2 text-left font-medium text-muted-foreground">Timestamp</th>
              <th className="px-4 py-2 text-left font-medium text-muted-foreground">Hash</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {references.map((ref, i) => (
              <tr key={i} className="hover:bg-muted/20">
                <td className="px-4 py-2 font-medium">{ref.source}</td>
                <td className="px-4 py-2 font-mono text-muted-foreground">{ref.reading}</td>
                <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{ref.timestamp}</td>
                <td className="px-4 py-2">
                  <code className="flex items-center gap-1 text-xs text-primary">
                    {ref.hash}
                    <ExternalLink className="h-3 w-3" />
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
