import { TelemetryGrid } from "@/components/app/ingest/telemetry-grid"
import { SignalSummary } from "@/components/app/ingest/signal-summary"
import { SourceReliability } from "@/components/app/ingest/source-reliability"

export default function DataIngestPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Ingest</h1>
          <p className="text-sm text-muted-foreground">Live telemetry and signal monitoring</p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-1.5">
          <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
          <span className="text-sm font-mono">LIVE</span>
        </div>
      </div>

      {/* Signal Summary Cards */}
      <SignalSummary />

      {/* Main Grid: Telemetry + Source Reliability */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TelemetryGrid />
        </div>
        <div>
          <SourceReliability />
        </div>
      </div>
    </div>
  )
}
