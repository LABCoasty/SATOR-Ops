"use client"

import { useState, useEffect } from "react"
import { AlertTriangle, CheckCircle, Clock, ArrowRight, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SimulationDecision } from "@/contexts/simulation-context"

interface Scenario2DecisionOverlayProps {
  decisions: SimulationDecision[]
  onSubmitDecision: (decisionId: string, response: string) => Promise<boolean>
}

export function Scenario2DecisionOverlay({
  decisions,
  onSubmitDecision
}: Scenario2DecisionOverlayProps) {
  const [selectedResponses, setSelectedResponses] = useState<Record<string, string>>({})
  const [submittingDecisions, setSubmittingDecisions] = useState<Set<string>>(new Set())
  const [dismissedDecisions, setDismissedDecisions] = useState<Set<string>>(new Set())

  // Filter out dismissed decisions
  const visibleDecisions = decisions.filter(d => !dismissedDecisions.has(d.decision_id))

  if (visibleDecisions.length === 0) return null

  const handleSelectResponse = (decisionId: string, response: string) => {
    setSelectedResponses(prev => ({ ...prev, [decisionId]: response }))
  }

  const handleSubmitDecision = async (decisionId: string) => {
    const response = selectedResponses[decisionId]
    if (!response) return

    setSubmittingDecisions(prev => new Set(prev).add(decisionId))
    const success = await onSubmitDecision(decisionId, response)
    setSubmittingDecisions(prev => {
      const next = new Set(prev)
      next.delete(decisionId)
      return next
    })
    
    if (success) {
      // Remove from view
      setDismissedDecisions(prev => new Set(prev).add(decisionId))
    }
  }

  const handleDismiss = (decisionId: string) => {
    setDismissedDecisions(prev => new Set(prev).add(decisionId))
  }

  // Get the most recent decision to show
  const currentDecision = visibleDecisions[visibleDecisions.length - 1]

  return (
    <div className="absolute inset-0 z-10">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm rounded-lg" />
      
      {/* Decision Card */}
      <div className="absolute inset-2 flex flex-col animate-in zoom-in-95 fade-in duration-300">
        <DecisionCard
          decision={currentDecision}
          selectedResponse={selectedResponses[currentDecision.decision_id]}
          onSelectResponse={(response) => handleSelectResponse(currentDecision.decision_id, response)}
          onSubmit={() => handleSubmitDecision(currentDecision.decision_id)}
          onDismiss={() => handleDismiss(currentDecision.decision_id)}
          isSubmitting={submittingDecisions.has(currentDecision.decision_id)}
          pendingCount={visibleDecisions.length}
        />
      </div>
    </div>
  )
}

interface DecisionCardProps {
  decision: SimulationDecision
  selectedResponse: string | undefined
  onSelectResponse: (response: string) => void
  onSubmit: () => void
  onDismiss: () => void
  isSubmitting: boolean
  pendingCount: number
}

function DecisionCard({
  decision,
  selectedResponse,
  onSelectResponse,
  onSubmit,
  onDismiss,
  isSubmitting,
  pendingCount
}: DecisionCardProps) {
  const [timeLeft, setTimeLeft] = useState<number | null>(decision.expires_in_sec)

  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [timeLeft])

  const isExpired = timeLeft !== null && timeLeft <= 0
  const isUrgent = timeLeft !== null && timeLeft <= 10

  return (
    <div
      className={cn(
        "flex-1 flex flex-col rounded-lg border-2 bg-card overflow-hidden",
        decision.severity === "critical" && "border-destructive",
        decision.severity === "warning" && "border-warning",
        decision.severity === "info" && "border-primary",
        isUrgent && "animate-pulse"
      )}
    >
      {/* Header */}
      <div
        className={cn(
          "px-4 py-3 flex items-start justify-between gap-2",
          decision.severity === "critical" && "bg-destructive/10",
          decision.severity === "warning" && "bg-warning/10",
          decision.severity === "info" && "bg-primary/10"
        )}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <AlertTriangle
              className={cn(
                "h-4 w-4 flex-shrink-0",
                decision.severity === "critical" && "text-destructive",
                decision.severity === "warning" && "text-warning",
                decision.severity === "info" && "text-primary"
              )}
            />
            <Badge
              variant={decision.severity === "critical" ? "destructive" : "secondary"}
              className="text-xs"
            >
              {decision.severity.toUpperCase()}
            </Badge>
            {pendingCount > 1 && (
              <Badge variant="outline" className="text-xs">
                +{pendingCount - 1} more
              </Badge>
            )}
            {timeLeft !== null && (
              <span
                className={cn(
                  "text-xs font-mono px-1.5 py-0.5 rounded ml-auto",
                  isExpired && "bg-destructive/20 text-destructive",
                  isUrgent && !isExpired && "bg-warning/20 text-warning",
                  !isUrgent && !isExpired && "bg-muted text-muted-foreground"
                )}
              >
                <Clock className="h-3 w-3 inline mr-1" />
                {isExpired ? "EXPIRED" : `${timeLeft}s`}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-sm mt-2">{decision.title}</h3>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 flex-shrink-0 -mt-1 -mr-1"
          onClick={onDismiss}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <p className="text-xs text-muted-foreground">{decision.description}</p>

        <div className="bg-muted/50 rounded-md p-3">
          <p className="text-xs font-medium mb-2">{decision.prompt}</p>
          
          <div className="space-y-1.5">
            {decision.options.map((option) => (
              <button
                key={option}
                onClick={() => onSelectResponse(option)}
                disabled={isExpired}
                className={cn(
                  "w-full flex items-center gap-2 rounded border px-3 py-2 text-left text-xs transition-all",
                  selectedResponse === option
                    ? "border-primary bg-primary/10"
                    : "border-border hover:bg-muted",
                  isExpired && "opacity-50 cursor-not-allowed"
                )}
              >
                <div
                  className={cn(
                    "h-3.5 w-3.5 rounded-full border-2 flex items-center justify-center flex-shrink-0",
                    selectedResponse === option
                      ? "border-primary bg-primary"
                      : "border-muted-foreground"
                  )}
                >
                  {selectedResponse === option && (
                    <CheckCircle className="h-2 w-2 text-primary-foreground" />
                  )}
                </div>
                <span className="flex-1">{option}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-border px-4 py-3">
        <Button
          size="sm"
          onClick={onSubmit}
          disabled={!selectedResponse || isSubmitting || isExpired}
          className="w-full gap-2"
        >
          {isSubmitting ? "Submitting..." : "Submit Decision"}
          <ArrowRight className="h-3 w-3" />
        </Button>
        <p className="text-[10px] text-muted-foreground text-center mt-2">
          Decision recorded in audit trail
        </p>
      </div>
    </div>
  )
}
