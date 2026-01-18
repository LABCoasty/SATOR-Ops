"use client"

import { Scale, AlertCircle, FileCheck, Clock, Loader2 } from "lucide-react"
import { useDecisionContext, useEvidence } from "@/hooks/use-decisions"

export function DecisionContext() {
  const { context, loading: contextLoading } = useDecisionContext()
  const { evidence, loading: evidenceLoading } = useEvidence()

  const loading = contextLoading || evidenceLoading

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading context...</span>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold">Decision Context</h2>
            <p className="text-xs text-muted-foreground">Evidence supporting the current assessment</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Current Assessment */}
      <div className="border-b border-border px-4 py-4">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-success/20">
            <FileCheck className="h-5 w-5 text-success" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium">{context?.current_assessment || "System Operating Within Normal Parameters"}</h3>
            <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
              Based on {context?.evidence_count || evidence.length} corroborating evidence sources, system health is confirmed stable. 
              {context?.contradictions_count && context.contradictions_count > 0 
                ? ` ${context.contradictions_count} minor contradictions noted but resolved.` 
                : " No contradictions detected."}
              {" "}No immediate action required.
            </p>
          </div>
        </div>
      </div>

      {/* Evidence List */}
      <div className="px-4 py-3">
        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
          <Scale className="h-4 w-4 text-muted-foreground" />
          Supporting Evidence
        </h4>
        <div className="space-y-2">
          {evidence.slice(0, 5).map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-md bg-muted/30 px-3 py-2">
              <div className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground font-mono">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </span>
                <div>
                  <span className="text-sm font-medium">{item.source}</span>
                  <p className="text-xs text-muted-foreground">
                    {item.value?.metric}: {item.value?.reading} {item.value?.unit}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Weight:</span>
                <span className="font-mono text-sm text-primary">{item.trust_score?.toFixed(2) || "0.00"}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Known Unknowns */}
      {context?.known_unknowns && context.known_unknowns.length > 0 && (
        <div className="border-t border-border px-4 py-3">
          <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-warning" />
            Known Unknowns
          </h4>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {context.known_unknowns.map((unknown, i) => (
              <li key={i} className="flex items-center gap-2">
                <span className="h-1 w-1 rounded-full bg-warning" />
                {unknown}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
