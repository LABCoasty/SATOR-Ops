"use client"

import { CheckCircle, User, Clock, MapPin } from "lucide-react"

export function DecisionSummary() {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-semibold">Decision Summary</h2>
      </div>

      <div className="p-4 space-y-4">
        {/* Outcome */}
        <div className="flex items-start gap-4 rounded-md bg-success/10 border border-success/20 p-4">
          <CheckCircle className="h-5 w-5 text-success mt-0.5" />
          <div>
            <h3 className="font-medium text-success">Decision: Continue Normal Operations</h3>
            <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
              Based on analysis of 47 active signals from 12 sources, system health has been verified as stable. Minor
              anomalies detected but resolved within acceptable parameters. No escalation required.
            </p>
          </div>
        </div>

        {/* Metadata */}
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-3 rounded-md bg-muted/30 px-3 py-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Operator</p>
              <p className="text-sm font-medium">System Auto-Assessment</p>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-md bg-muted/30 px-3 py-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Assessment Window</p>
              <p className="text-sm font-medium">14:28:00 – 14:41:00</p>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-md bg-muted/30 px-3 py-2">
            <MapPin className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Facility</p>
              <p className="text-sm font-medium">Station Alpha-7</p>
            </div>
          </div>
        </div>

        {/* Key Findings */}
        <div>
          <h4 className="text-sm font-medium mb-2">Key Findings</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
              Core temperature stable at 72.4°C with minor upward trend
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
              Flow rate anomaly at 14:32 resolved through sensor reconciliation
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
              Vibration levels within threshold despite elevated readings
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-warning shrink-0" />
              Remote Station C remains offline — external verification unavailable
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
