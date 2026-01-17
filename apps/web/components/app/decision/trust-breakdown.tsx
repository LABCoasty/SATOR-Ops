"use client"

import { Scale, AlertCircle, HelpCircle, FileText, Info } from "lucide-react"
import { cn } from "@/lib/utils"

interface TrustFactor {
  label: string
  value: number
  impact: "positive" | "negative" | "neutral"
  icon: typeof Scale
}

const factors: TrustFactor[] = [
  { label: "Evidence Corroboration", value: 0.92, impact: "positive", icon: Scale },
  { label: "Source Reliability Avg", value: 0.86, impact: "positive", icon: FileText },
  { label: "Contradiction Penalty", value: -0.08, impact: "negative", icon: AlertCircle },
  { label: "Data Freshness", value: 0.95, impact: "positive", icon: Info },
  { label: "Unknown Factors", value: -0.05, impact: "negative", icon: HelpCircle },
]

const reasonCodes = [
  { code: "TR_0x12A", description: "High sensor corroboration" },
  { code: "TR_0x08B", description: "Minor flow sensor divergence" },
  { code: "TR_0x04C", description: "External feed staleness" },
]

export function TrustBreakdown() {
  const compositeScore = 0.87

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-semibold">Trust Breakdown</h2>
        <p className="text-xs text-muted-foreground">How confidence is computed</p>
      </div>

      {/* Composite Score */}
      <div className="border-b border-border px-4 py-4">
        <div className="text-center">
          <span className="text-xs text-muted-foreground uppercase tracking-wide">Composite Trust Score</span>
          <p
            className={cn(
              "text-4xl font-bold font-mono mt-1",
              compositeScore >= 0.85 ? "text-success" : compositeScore >= 0.7 ? "text-warning" : "text-destructive",
            )}
          >
            {compositeScore.toFixed(2)}
          </p>
          <div className="mt-3 h-2 rounded-full bg-muted overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                compositeScore >= 0.85 ? "bg-success" : compositeScore >= 0.7 ? "bg-warning" : "bg-destructive",
              )}
              style={{ width: `${compositeScore * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Factor Breakdown */}
      <div className="px-4 py-3 space-y-3">
        <h4 className="text-sm font-medium">Contributing Factors</h4>
        {factors.map((factor) => (
          <div key={factor.label} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <factor.icon
                className={cn(
                  "h-4 w-4",
                  factor.impact === "positive" && "text-success",
                  factor.impact === "negative" && "text-warning",
                  factor.impact === "neutral" && "text-muted-foreground",
                )}
              />
              <span className="text-sm text-muted-foreground">{factor.label}</span>
            </div>
            <span
              className={cn(
                "font-mono text-sm",
                factor.impact === "positive" && "text-success",
                factor.impact === "negative" && "text-warning",
                factor.impact === "neutral" && "text-foreground",
              )}
            >
              {factor.value >= 0 ? "+" : ""}
              {typeof factor.value === "number" && factor.value < 1 && factor.value > -1
                ? factor.value.toFixed(2)
                : factor.value}
            </span>
          </div>
        ))}
      </div>

      {/* Reason Codes */}
      <div className="border-t border-border px-4 py-3">
        <h4 className="text-sm font-medium mb-2">Reason Codes</h4>
        <div className="space-y-2">
          {reasonCodes.map((rc) => (
            <div key={rc.code} className="flex items-center justify-between rounded-md bg-muted/30 px-2 py-1.5">
              <code className="text-xs font-mono text-primary">{rc.code}</code>
              <span className="text-xs text-muted-foreground">{rc.description}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
