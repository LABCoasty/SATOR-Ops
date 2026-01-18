"use client"

import { useState } from "react"
import { 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  MessageSquare, 
  Lightbulb, 
  ChevronDown, 
  ChevronUp,
  User,
  FileText,
  Send,
  Timer
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useOptionalSimulationContext } from "@/contexts/simulation-context"

export function OperatorDecisionsLog() {
  const simulation = useOptionalSimulationContext()
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [explanations, setExplanations] = useState<Record<string, string>>({})
  const [recommendations, setRecommendations] = useState<Record<string, string>>({})

  const decisions = simulation?.completedDecisions || []

  const handleSaveDocumentation = (decisionId: string) => {
    simulation?.updateDecisionDocumentation(
      decisionId,
      explanations[decisionId],
      recommendations[decisionId]
    )
  }

  if (decisions.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-center gap-3 mb-4">
          <User className="h-5 w-5 text-muted-foreground" />
          <h2 className="font-semibold">Operator Decisions</h2>
        </div>
        <p className="text-sm text-muted-foreground text-center py-8">
          {simulation?.isRunning 
            ? "No decisions recorded yet. Decisions will appear here as you respond to prompts."
            : "Start a simulation to see operator decisions."}
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <User className="h-5 w-5 text-primary" />
            <div>
              <h2 className="font-semibold">Operator Decisions</h2>
              <p className="text-xs text-muted-foreground">{decisions.length} decision(s) recorded</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>Audit trail active</span>
          </div>
        </div>
      </div>

      <div className="divide-y divide-border max-h-[500px] overflow-y-auto">
        {decisions.map((decision) => (
          <div key={decision.decision_id} className="px-4 py-3">
            {/* Decision Header */}
            <button
              onClick={() => setExpandedId(expandedId === decision.decision_id ? null : decision.decision_id)}
              className="w-full text-left"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className={cn(
                    "mt-0.5 h-8 w-8 rounded-full flex items-center justify-center",
                    decision.severity === "critical" && "bg-destructive/20",
                    decision.severity === "warning" && "bg-warning/20",
                    decision.severity === "info" && "bg-primary/20"
                  )}>
                    {decision.severity === "critical" ? (
                      <AlertTriangle className="h-4 w-4 text-destructive" />
                    ) : decision.severity === "warning" ? (
                      <AlertTriangle className="h-4 w-4 text-warning" />
                    ) : (
                      <CheckCircle className="h-4 w-4 text-primary" />
                    )}
                  </div>
                  <div>
                    <h4 className="font-medium text-sm">{decision.title}</h4>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      at {decision.time_sec.toFixed(0)}s • Response: <span className="text-primary font-medium">{decision.response}</span>
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Timer className="h-3 w-3" />
                        Response time: {decision.response_time_sec.toFixed(1)}s
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {(decision.explanation || decision.recommendation) && (
                    <span className="text-xs text-success flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      Documented
                    </span>
                  )}
                  {expandedId === decision.decision_id ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
              </div>
            </button>

            {/* Expanded Content */}
            {expandedId === decision.decision_id && (
              <div className="mt-4 ml-11 space-y-4">
                {/* Decision Details */}
                <div className="rounded-md bg-muted/50 p-3">
                  <p className="text-sm text-muted-foreground">{decision.description}</p>
                </div>

                {/* Explanation Input */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium mb-2">
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    Explain Your Decision
                  </label>
                  <textarea
                    value={explanations[decision.decision_id] ?? decision.explanation ?? ""}
                    onChange={(e) => setExplanations({ ...explanations, [decision.decision_id]: e.target.value })}
                    placeholder="Why did you make this decision? What factors did you consider?"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring min-h-[80px] resize-none"
                  />
                </div>

                {/* Recommendation Input */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium mb-2">
                    <Lightbulb className="h-4 w-4 text-warning" />
                    Your Recommendation
                  </label>
                  <textarea
                    value={recommendations[decision.decision_id] ?? decision.recommendation ?? ""}
                    onChange={(e) => setRecommendations({ ...recommendations, [decision.decision_id]: e.target.value })}
                    placeholder="Based on this decision, what do you recommend for future similar situations?"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring min-h-[80px] resize-none"
                  />
                </div>

                {/* Save Button */}
                <div className="flex justify-end">
                  <Button 
                    size="sm" 
                    onClick={() => handleSaveDocumentation(decision.decision_id)}
                    className="gap-2"
                  >
                    <Send className="h-4 w-4" />
                    Save Documentation
                  </Button>
                </div>

                {/* Saved Documentation Display */}
                {(decision.explanation || decision.recommendation) && (
                  <div className="border-t border-border pt-4 space-y-3">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">Saved Documentation</p>
                    {decision.explanation && (
                      <div className="rounded-md bg-primary/5 border border-primary/20 p-3">
                        <p className="text-xs text-primary font-medium mb-1">Explanation</p>
                        <p className="text-sm">{decision.explanation}</p>
                      </div>
                    )}
                    {decision.recommendation && (
                      <div className="rounded-md bg-warning/5 border border-warning/20 p-3">
                        <p className="text-xs text-warning font-medium mb-1">Recommendation</p>
                        <p className="text-sm">{decision.recommendation}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary Footer */}
      <div className="border-t border-border px-4 py-2 bg-muted/30">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {decisions.filter(d => d.explanation || d.recommendation).length} of {decisions.length} documented
          </span>
          <span>
            Avg response time: {decisions.length > 0 
              ? (decisions.reduce((sum, d) => sum + d.response_time_sec, 0) / decisions.length).toFixed(1)
              : 0}s
          </span>
        </div>
      </div>
    </div>
  )
}
