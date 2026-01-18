"use client"

import { useState, useEffect } from "react"
import { AlertTriangle, Clock, CheckCircle, XCircle, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface DecisionOption {
  label: string
  value: string
}

export interface DecisionPromptData {
  decision_id: string
  event_id: string
  time_sec: number
  title: string
  description: string
  severity: "info" | "warning" | "critical"
  decision_type: "acknowledge" | "binary" | "multi_choice" | "escalate"
  options: string[]
  prompt: string
  expires_in_sec?: number | null
}

interface DecisionPromptProps {
  decision: DecisionPromptData
  onSubmit: (decisionId: string, response: string) => void
  onDismiss?: () => void
}

export function DecisionPrompt({ decision, onSubmit, onDismiss }: DecisionPromptProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [timeLeft, setTimeLeft] = useState<number | null>(decision.expires_in_sec ?? null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Countdown timer
  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [timeLeft])

  const handleSubmit = async () => {
    if (!selectedOption) return
    setIsSubmitting(true)
    await onSubmit(decision.decision_id, selectedOption)
    setIsSubmitting(false)
  }

  const getSeverityStyles = () => {
    switch (decision.severity) {
      case "critical":
        return {
          border: "status-critical-border",
          bg: "status-critical-bg",
          icon: <AlertTriangle className="h-6 w-6 status-critical-text" />,
          badge: "status-critical-bg status-critical-text"
        }
      case "warning":
        return {
          border: "status-risk-border",
          bg: "status-risk-bg",
          icon: <AlertTriangle className="h-6 w-6 status-risk-text" />,
          badge: "status-risk-bg status-risk-text"
        }
      default:
        // Info/default uses uncertain (yellow) - requires human judgment
        return {
          border: "status-uncertain-border",
          bg: "status-uncertain-bg",
          icon: <CheckCircle className="h-6 w-6 status-uncertain-text" />,
          badge: "status-uncertain-bg status-uncertain-text"
        }
    }
  }

  const styles = getSeverityStyles()
  const isExpired = timeLeft !== null && timeLeft <= 0
  const isUrgent = timeLeft !== null && timeLeft <= 10

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div
        className={cn(
          "w-full max-w-lg rounded-lg border-2 bg-card shadow-xl",
          styles.border,
          isUrgent && "animate-pulse"
        )}
      >
        {/* Header */}
        <div className={cn("rounded-t-lg px-6 py-4", styles.bg)}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {styles.icon}
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold">{decision.title}</h2>
                  <span className={cn("rounded px-2 py-0.5 text-xs font-medium uppercase", styles.badge)}>
                    {decision.severity}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Event at {decision.time_sec.toFixed(0)}s into scenario
                </p>
              </div>
            </div>
            {timeLeft !== null && (
              <div
                className={cn(
                  "flex items-center gap-1 rounded-full px-3 py-1 text-sm font-mono",
                  isExpired ? "bg-destructive/20 text-destructive" :
                  isUrgent ? "bg-warning/20 text-warning animate-pulse" :
                  "bg-muted text-muted-foreground"
                )}
              >
                <Clock className="h-4 w-4" />
                {isExpired ? "EXPIRED" : `${timeLeft}s`}
              </div>
            )}
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          <p className="text-sm text-muted-foreground leading-relaxed">
            {decision.description}
          </p>

          <div className="rounded-md bg-muted/50 p-4">
            <p className="text-sm font-medium mb-3">{decision.prompt}</p>
            
            <div className="space-y-2">
              {decision.options.map((option, index) => (
                <button
                  key={option}
                  onClick={() => setSelectedOption(option)}
                  disabled={isExpired}
                  className={cn(
                    "w-full flex items-center gap-3 rounded-md border px-4 py-3 text-left text-sm transition-all",
                    selectedOption === option
                      ? "border-primary bg-primary/10 text-foreground"
                      : "border-border bg-card hover:bg-muted hover:border-muted-foreground/30",
                    isExpired && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <div
                    className={cn(
                      "h-5 w-5 rounded-full border-2 flex items-center justify-center",
                      selectedOption === option
                        ? "border-primary bg-primary"
                        : "border-muted-foreground"
                    )}
                  >
                    {selectedOption === option && (
                      <CheckCircle className="h-3 w-3 text-primary-foreground" />
                    )}
                  </div>
                  <span className="flex-1">{option}</span>
                  <span className="text-xs text-muted-foreground">
                    {index + 1}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border px-6 py-4">
          <p className="text-xs text-muted-foreground">
            Your decision will be recorded in the audit trail
          </p>
          <div className="flex items-center gap-2">
            {onDismiss && (
              <Button variant="ghost" size="sm" onClick={onDismiss}>
                Skip
              </Button>
            )}
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={!selectedOption || isSubmitting || isExpired}
              className="gap-2"
            >
              {isSubmitting ? "Submitting..." : "Submit Decision"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Toast-style mini notification for new events
export function EventToast({ 
  event, 
  onClose 
}: { 
  event: { title: string; description: string; severity: string; time_sec: number }
  onClose: () => void 
}) {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div
      className={cn(
        "fixed bottom-24 right-6 z-40 w-80 rounded-lg border bg-card p-4 shadow-lg animate-in slide-in-from-right",
        event.severity === "critical" && "border-destructive",
        event.severity === "warning" && "border-warning"
      )}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle
          className={cn(
            "h-5 w-5 mt-0.5",
            event.severity === "critical" && "text-destructive",
            event.severity === "warning" && "text-warning",
            event.severity === "info" && "text-primary"
          )}
        />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-sm">{event.title}</h4>
            <span className="text-xs text-muted-foreground">{event.time_sec.toFixed(0)}s</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">{event.description}</p>
        </div>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground"
        >
          <XCircle className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
