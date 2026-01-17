"use client"

import { CheckCircle } from "lucide-react"

export function DecisionOutcome() {
  return (
    <div className="border-b border-border p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-success/20">
          <CheckCircle className="h-5 w-5 text-success" />
        </div>
        <div>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Decision Outcome</span>
          <h2 className="mt-1 text-xl font-bold text-success">Continue Normal Operations</h2>
          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
            Assessment window 14:28:00 – 14:41:00 UTC on January 17, 2026. System verified stable with high confidence.
          </p>
        </div>
      </div>
    </div>
  )
}
