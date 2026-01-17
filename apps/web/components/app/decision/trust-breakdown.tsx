"use client"

import { Scale, AlertCircle, HelpCircle, FileText, Info, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTrustBreakdown } from "@/hooks/use-decisions"

const iconMap: Record<string, typeof Scale> = {
  "Evidence Corroboration": Scale,
  "Source Reliability Avg": FileText,
  "Contradiction Penalty": AlertCircle,
  "Data Freshness": Info,
  "Unknown Factors": HelpCircle,
}

export function TrustBreakdown() {
  const { breakdown, loading, error } = useTrustBreakdown()

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !breakdown) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive text-sm">
        Failed to load trust breakdown
      </div>
    )
  }

  const compositeScore = breakdown.composite_score

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
        {breakdown.factors.map((factor) => {
          const IconComponent = iconMap[factor.label] || Scale
          return (
            <div key={factor.label} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <IconComponent
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
          )
        })}
      </div>

      {/* Reason Codes */}
      <div className="border-t border-border px-4 py-3">
        <h4 className="text-sm font-medium mb-2">Reason Codes</h4>
        <div className="space-y-2">
          {breakdown.reason_codes.map((rc) => (
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
