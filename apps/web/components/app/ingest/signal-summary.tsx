"use client"

import { Activity, AlertTriangle, CheckCircle, HelpCircle } from "lucide-react"

const summaryCards = [
  {
    label: "Active Signals",
    value: "47",
    subtext: "12 sources reporting",
    icon: Activity,
    status: "normal" as const,
  },
  {
    label: "Healthy",
    value: "41",
    subtext: "Within expected range",
    icon: CheckCircle,
    status: "success" as const,
  },
  {
    label: "Warnings",
    value: "4",
    subtext: "Deviation detected",
    icon: AlertTriangle,
    status: "warning" as const,
  },
  {
    label: "Unknown",
    value: "2",
    subtext: "Awaiting data",
    icon: HelpCircle,
    status: "muted" as const,
  },
]

const statusColors = {
  normal: "text-foreground",
  success: "text-success",
  warning: "text-warning",
  muted: "text-muted-foreground",
}

export function SignalSummary() {
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
