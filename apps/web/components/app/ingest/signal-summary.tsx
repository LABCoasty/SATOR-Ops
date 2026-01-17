"use client"

import { Activity, AlertTriangle, CheckCircle, HelpCircle, Loader2 } from "lucide-react"
import { useSignalSummary } from "@/hooks/use-telemetry"

const statusColors = {
  normal: "text-foreground",
  success: "text-success",
  warning: "text-warning",
  muted: "text-muted-foreground",
}

export function SignalSummary() {
  const { summary, loading, error } = useSignalSummary()

  if (loading) {
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

  if (error || !summary) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
        Failed to load signal summary
      </div>
    )
  }

  const summaryCards = [
    {
      label: "Active Signals",
      value: summary.active_signals.toString(),
      subtext: `${summary.sources_reporting} sources reporting`,
      icon: Activity,
      status: "normal" as const,
    },
    {
      label: "Healthy",
      value: summary.healthy.toString(),
      subtext: "Within expected range",
      icon: CheckCircle,
      status: "success" as const,
    },
    {
      label: "Warnings",
      value: summary.warnings.toString(),
      subtext: "Deviation detected",
      icon: AlertTriangle,
      status: "warning" as const,
    },
    {
      label: "Unknown",
      value: summary.unknown.toString(),
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
