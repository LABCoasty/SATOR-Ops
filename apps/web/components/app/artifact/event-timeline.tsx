"use client"

import { cn } from "@/lib/utils"
import { AlertTriangle, CheckCircle, Info } from "lucide-react"

interface TimelineEvent {
  time: string
  title: string
  description: string
  type: "normal" | "anomaly" | "resolution" | "info"
}

const events: TimelineEvent[] = [
  {
    time: "14:28:00",
    title: "Assessment Initiated",
    description: "Baseline telemetry captured. All 12 sources reporting.",
    type: "info",
  },
  {
    time: "14:30:15",
    title: "Anomaly Detected",
    description: "Flow rate deviation observed. Sensors A and B reporting divergent values.",
    type: "anomaly",
  },
  {
    time: "14:32:42",
    title: "Contradiction Flagged",
    description: "Flow Sensor A (234 L/min) vs Flow Sensor B (248 L/min). Trust score adjusted.",
    type: "anomaly",
  },
  {
    time: "14:35:08",
    title: "Resolution Applied",
    description: "Weighted average calculation applied. Sensor B flagged for calibration review.",
    type: "resolution",
  },
  {
    time: "14:38:30",
    title: "System Stabilized",
    description: "All signals within normal range. Trust score recovered to 0.87.",
    type: "normal",
  },
  {
    time: "14:41:00",
    title: "Artifact Generated",
    description: "Decision artifact compiled with full evidence chain and audit trail.",
    type: "info",
  },
]

const typeStyles = {
  normal: { icon: CheckCircle, color: "text-success", bg: "bg-success" },
  anomaly: { icon: AlertTriangle, color: "text-warning", bg: "bg-warning" },
  resolution: { icon: CheckCircle, color: "text-primary", bg: "bg-primary" },
  info: { icon: Info, color: "text-muted-foreground", bg: "bg-muted-foreground" },
}

export function EventTimeline() {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-semibold">Event Timeline</h2>
        <p className="text-xs text-muted-foreground">Chronological record of the assessment window</p>
      </div>

      <div className="p-4">
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[19px] top-2 bottom-2 w-px bg-border" />

          {/* Events */}
          <div className="space-y-4">
            {events.map((event, i) => {
              const style = typeStyles[event.type]
              const Icon = style.icon
              return (
                <div key={i} className="flex gap-4">
                  <div className="relative z-10">
                    <div
                      className={cn(
                        "flex h-10 w-10 items-center justify-center rounded-full border-2 border-card bg-card",
                        style.color,
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-muted-foreground">{event.time}</span>
                      <span className="font-medium">{event.title}</span>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{event.description}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
