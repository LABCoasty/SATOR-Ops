"use client"

import { HelpCircle } from "lucide-react"

const unknowns = [
  {
    item: "Remote Station C",
    status: "Offline for 15+ minutes",
    impact: "External environmental conditions unverified",
  },
  {
    item: "Legacy System Link",
    status: "Degraded connection",
    impact: "Historical baseline comparison limited",
  },
]

export function KnownUnknowns() {
  return (
    <div className="p-6">
      <div className="flex items-center gap-2 mb-4">
        <HelpCircle className="h-4 w-4 text-warning" />
        <h3 className="font-semibold">Known Unknowns</h3>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        The following information gaps were identified but could not be resolved during the assessment window.
      </p>
      <div className="space-y-3">
        {unknowns.map((unknown) => (
          <div key={unknown.item} className="rounded-md border border-warning/30 bg-warning/5 p-3">
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm">{unknown.item}</span>
              <span className="text-xs text-warning">{unknown.status}</span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{unknown.impact}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
