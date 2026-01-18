"use client"

import { useState, useEffect } from "react"
import { AlertTriangle, Clock, CheckCircle, ArrowRight, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SimulationDecision } from "@/contexts/simulation-context"

interface Scenario1DecisionPanelProps {
    decisions: SimulationDecision[]
    onSubmitDecision: (decisionId: string, response: string) => Promise<boolean>
    currentTimeSec: number
}

export function Scenario1DecisionPanel({
    decisions,
    onSubmitDecision,
    currentTimeSec
}: Scenario1DecisionPanelProps) {
    const [selectedResponses, setSelectedResponses] = useState<Record<string, string>>({})
    const [submittingDecisions, setSubmittingDecisions] = useState<Set<string>>(new Set())
    const [dismissedDecisions, setDismissedDecisions] = useState<Set<string>>(new Set())

    // Filter out dismissed decisions and get pending ones
    const visibleDecisions = decisions.filter(d => !dismissedDecisions.has(d.decision_id))
    const currentDecision = visibleDecisions[visibleDecisions.length - 1]

    // Track time left for current decision
    const [timeLeft, setTimeLeft] = useState<number | null>(
        currentDecision?.expires_in_sec ?? null
    )

    // Reset timer when decision changes
    useEffect(() => {
        if (currentDecision) {
            setTimeLeft(currentDecision.expires_in_sec ?? null)
        }
    }, [currentDecision?.decision_id])

    // Countdown timer
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

    const handleSelectResponse = (decisionId: string, response: string) => {
        setSelectedResponses(prev => ({ ...prev, [decisionId]: response }))
    }

    const handleSubmitDecision = async (decisionId: string) => {
        const response = selectedResponses[decisionId]
        if (!response) return

        setSubmittingDecisions(prev => new Set(prev).add(decisionId))
        try {
            await onSubmitDecision(decisionId, response)
            setDismissedDecisions(prev => new Set(prev).add(decisionId))
            setSelectedResponses(prev => {
                const next = { ...prev }
                delete next[decisionId]
                return next
            })
        } finally {
            setSubmittingDecisions(prev => {
                const next = new Set(prev)
                next.delete(decisionId)
                return next
            })
        }
    }

    const handleDismiss = (decisionId: string) => {
        setDismissedDecisions(prev => new Set(prev).add(decisionId))
        setSelectedResponses(prev => {
            const next = { ...prev }
            delete next[decisionId]
            return next
        })
    }

    if (!currentDecision) {
        return null
    }

    const selectedResponse = selectedResponses[currentDecision.decision_id]
    const isSubmitting = submittingDecisions.has(currentDecision.decision_id)

    const isExpired = timeLeft !== null && timeLeft <= 0
    const isUrgent = timeLeft !== null && timeLeft <= 10

    const getSeverityStyles = () => {
        switch (currentDecision.severity) {
            case "critical":
                return {
                    border: "border-destructive",
                    bg: "bg-destructive/10",
                    icon: <AlertTriangle className="h-6 w-6 text-destructive" />,
                    badge: "bg-destructive text-destructive-foreground"
                }
            case "warning":
                return {
                    border: "border-warning",
                    bg: "bg-warning/10",
                    icon: <AlertTriangle className="h-6 w-6 text-warning" />,
                    badge: "bg-warning text-warning-foreground"
                }
            default:
                return {
                    border: "border-primary",
                    bg: "bg-primary/10",
                    icon: <CheckCircle className="h-6 w-6 text-primary" />,
                    badge: "bg-primary text-primary-foreground"
                }
        }
    }

    const styles = getSeverityStyles()

    return (
        <div className="rounded-lg border border-border bg-card overflow-hidden animate-in fade-in duration-500">
            {/* Header */}
            <div className={cn("border-b border-border px-6 py-4", styles.bg)}>
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        {styles.icon}
                        <div>
                            <div className="flex items-center gap-2">
                                <h2 className="text-lg font-bold">{currentDecision.title}</h2>
                                <Badge variant={currentDecision.severity === "critical" ? "destructive" : "secondary"} className="text-xs">
                                    {currentDecision.severity.toUpperCase()}
                                </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                                Event at {currentDecision.time_sec.toFixed(0)}s into scenario
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
                    {currentDecision.description}
                </p>

                <div className="rounded-md bg-muted/50 p-4">
                    <p className="text-sm font-medium mb-3">{currentDecision.prompt}</p>

                    <div className="space-y-2">
                        {currentDecision.options.map((option, index) => (
                            <button
                                key={option}
                                onClick={() => handleSelectResponse(currentDecision.decision_id, option)}
                                disabled={isExpired}
                                className={cn(
                                    "w-full flex items-center gap-3 rounded-md border px-4 py-3 text-left text-sm transition-all",
                                    selectedResponse === option
                                        ? "border-primary bg-primary/10 text-foreground"
                                        : "border-border bg-card hover:bg-muted hover:border-muted-foreground/30",
                                    isExpired && "opacity-50 cursor-not-allowed"
                                )}
                            >
                                <div
                                    className={cn(
                                        "h-5 w-5 rounded-full border-2 flex items-center justify-center",
                                        selectedResponse === option
                                            ? "border-primary bg-primary"
                                            : "border-muted-foreground"
                                    )}
                                >
                                    {selectedResponse === option && (
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
                    {visibleDecisions.length > 1 && (
                        <span className="font-medium">{visibleDecisions.length - 1} more pending</span>
                    )}
                    {visibleDecisions.length === 1 && "Your decision will be recorded in the audit trail"}
                </p>
                <div className="flex items-center gap-2">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDismiss(currentDecision.decision_id)}
                        disabled={isSubmitting}
                    >
                        <X className="h-4 w-4 mr-1" />
                        Skip
                    </Button>
                    <Button
                        size="sm"
                        onClick={() => handleSubmitDecision(currentDecision.decision_id)}
                        disabled={!selectedResponse || isSubmitting || isExpired}
                        className="gap-2"
                    >
                        {isSubmitting ? "Submitting..." : "Submit Decision"}
                        <ArrowRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    )
}
