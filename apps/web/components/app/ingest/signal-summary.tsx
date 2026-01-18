"use client"

import { useMemo } from "react"
import { Activity, AlertTriangle, CheckCircle, HelpCircle } from "lucide-react"
import { useSignalSummary } from "@/hooks/use-telemetry"
import { useOptionalSimulationContext } from "@/contexts/simulation-context"

const statusColors = {
  normal: "text-foreground",
  success: "text-success",
  warning: "text-warning",
  muted: "text-muted-foreground",
}

export function SignalSummary() {
  const { summary: apiSummary, loading, error } = useSignalSummary()
  const simulation = useOptionalSimulationContext()

  // Calculate summary from simulation telemetry when running
  const simulationSummary = useMemo(() => {
    if (!simulation?.isRunning || !simulation?.telemetry?.channels) {
      return null
    }

    const channels = Object.values(simulation.telemetry.channels) as Array<{ status: string }>
    const healthy = channels.filter(c => c.status === "normal").length
    const warnings = channels.filter(c => c.status === "warning").length
    const critical = channels.filter(c => c.status === "critical").length
    const unknown = 0

    return {
      active_signals: channels.length * 7, // Simulate multiple signals per channel
      sources_reporting: 12,
      healthy: healthy * 6 + (7 - channels.length), // Scale up
      warnings: warnings + critical,
      unknown,
      critical,
      last_sync: "now",
      connected: true
    }
  }, [simulation?.isRunning, simulation?.telemetry])

  const summary = simulation?.isRunning && simulationSummary ? simulationSummary : apiSummary

  if (loading && !simulation?.isRunning) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-lg border border-border bg-card p-4 animate-pulse">
            <div className="h-4 bg-muted rounded w-24 mb-2" />
            <div className="h-8 bg-muted rounded w-16" />
          </div>
        ))}
      </div>
    )
  }

  if ((error || !summary) && !simulation?.isRunning) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
        Failed to load signal summary
      </div>
    )
  }

  // Use default values if no summary available
  const displaySummary = summary || {
    active_signals: 47,
    sources_reporting: 12,
    healthy: 41,
    warnings: 4,
    unknown: 2,
    critical: 0
  }

  const summaryCards = [
    {
      label: "Active Signals",
      value: displaySummary.active_signals.toString(),
      subtext: `${displaySummary.sources_reporting} sources reporting`,
      icon: Activity,
      status: "normal" as const,
    },
    {
      label: "Healthy",
      value: displaySummary.healthy.toString(),
      subtext: "Within expected range",
      icon: CheckCircle,
      status: "success" as const,
    },
    {
      label: "Warnings",
      value: displaySummary.warnings.toString(),
      subtext: displaySummary.warnings > 0 ? "Deviation detected" : "No deviations",
      icon: AlertTriangle,
      status: "warning" as const,
    },
    {
      label: "Unknown",
      value: displaySummary.unknown.toString(),
      subtext: "Awaiting data",
      icon: HelpCircle,
      status: "muted" as const,
    },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {summaryCards.map((card) => (
        <div key={card.label} className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{card.label}</span>
            <card.icon className={`h-4 w-4 ${statusColors[card.status]}`} />
          </div>
          <div className="mt-2">
            <span className={`text-2xl font-bold ${statusColors[card.status]}`}>{card.value}</span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{card.subtext}</p>
        </div>
      ))}
    </div>
  )
}
