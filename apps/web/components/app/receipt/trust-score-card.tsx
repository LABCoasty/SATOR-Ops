"use client"

import { cn } from "@/lib/utils"

const reasonCodes = [
  { code: "TR_0x12A", label: "High sensor corroboration", impact: "+0.12" },
  { code: "TR_0x08B", label: "Flow sensor divergence", impact: "-0.08" },
  { code: "TR_0x04C", label: "External feed staleness", impact: "-0.02" },
  { code: "TR_0x03D", label: "Offline source penalty", impact: "-0.05" },
]

export function TrustScoreCard() {
  const score = 0.87

  return (
    <div className="border-b border-border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Trust Score</h3>
        <span
          className={cn(
            "text-3xl font-bold font-mono",
            score >= 0.85 ? "text-success" : score >= 0.7 ? "text-warning" : "text-destructive",
          )}
        >
          {score.toFixed(2)}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-3 rounded-full bg-muted overflow-hidden mb-6">
        <div className="h-full rounded-full bg-success" style={{ width: `${score * 100}%` }} />
      </div>

      {/* Reason codes */}
      <div className="space-y-2">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Reason Codes</span>
        <div className="space-y-2 mt-2">
          {reasonCodes.map((rc) => (
            <div key={rc.code} className="flex items-center justify-between rounded-md bg-muted/30 px-3 py-2">
              <div className="flex items-center gap-3">
                <code className="text-xs font-mono text-primary">{rc.code}</code>
                <span className="text-sm text-muted-foreground">{rc.label}</span>
              </div>
              <span className={cn("font-mono text-sm", rc.impact.startsWith("+") ? "text-success" : "text-warning")}>
                {rc.impact}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
