"use client"

import { useCallback } from "react"
import { TelemetryGrid } from "@/components/app/ingest/telemetry-grid"
import { SignalSummary } from "@/components/app/ingest/signal-summary"
import { SourceReliability } from "@/components/app/ingest/source-reliability"
import { Scenario2VideoPanel } from "@/components/app/ingest/scenario2-video-panel"
import { Scenario2DecisionOverlay } from "@/components/app/ingest/scenario2-decision-overlay"
import { Scenario1DecisionPanel } from "@/components/app/ingest/scenario1-decision-panel"
import { useSimulationContext } from "@/contexts/simulation-context"
import { useVoiceCallContext } from "@/contexts/voice-call-context"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

// Vision scenarios show video panel after 5 seconds
const VISION_ALERT_DELAY_SEC = 5

// Helper to detect if a response is an escalation to supervisor
function isEscalationToSupervisor(response: string): boolean {
  const lowerResponse = response.toLowerCase()
  return (
    lowerResponse.includes("escalate to supervisor") ||
    lowerResponse.includes("escalate to manager") ||
    lowerResponse.includes("escalate to management") ||
    lowerResponse.includes("escalate to facility manager") ||
    lowerResponse.includes("escalate to utility management")
  )
}

export default function DataIngestPage() {
  const { 
    state: simState, 
    events, 
    decisions, 
    activeScenario, 
    isRunning,
    submitDecision 
  } = useSimulationContext()

  const { triggerCall } = useVoiceCallContext()

  // Wrap submitDecision to detect escalation and trigger voice call
  const handleSubmitDecision = useCallback(async (decisionId: string, response: string): Promise<boolean> => {
    // Find the decision to get its details for context
    const decision = decisions.find(d => d.decision_id === decisionId)
    
    // Submit the decision first
    const success = await submitDecision(decisionId, response)
    
    // If this is an escalation to supervisor, trigger the voice call
    if (success && isEscalationToSupervisor(response)) {
      triggerCall({
        currentPage: '/app/ingest',
        trustScore: simState?.trust_score,
        trustState: simState?.trust_score !== undefined 
          ? (simState.trust_score >= 0.8 ? 'high' : simState.trust_score >= 0.6 ? 'medium' : 'low')
          : undefined,
        decisionId: decisionId,
        decisionTitle: decision?.title,
        escalationType: response,
      })
    }
    
    return success
  }, [submitDecision, decisions, simState?.trust_score, triggerCall])

  // Calculate if vision panel (scenario 2, 3, or 4) should be visible
  const isScenario1 = activeScenario === "scenario1"
  const isScenario2 = activeScenario === "scenario2"
  const isScenario3 = activeScenario === "scenario3"
  const isScenario4 = activeScenario === "scenario4"
  const isVisionScenario = isScenario2 || isScenario3 || isScenario4
  const visionTimeReached = simState && simState.current_time_sec >= VISION_ALERT_DELAY_SEC
  const showVisionPanel = isVisionScenario && isRunning && visionTimeReached
  
  // For Scenario 1, show decision panel when there are active decisions
  const showScenario1DecisionPanel = isScenario1 && isRunning && decisions.length > 0

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Ingest</h1>
          <p className="text-sm text-muted-foreground">Live telemetry and signal monitoring</p>
        </div>
        <div className="flex items-center gap-2">
          {showVisionPanel && (
            <Badge 
              variant={isScenario2 ? "destructive" : "default"} 
              className={cn(
                "animate-pulse",
                isScenario3 && "bg-blue-500 text-white",
                isScenario4 && "bg-orange-500 text-white"
              )}
            >
              {isScenario2 && "VISION ACTIVE"}
              {isScenario3 && "WATER MONITORING"}
              {isScenario4 && "ARC FLASH ALERT"}
            </Badge>
          )}
          <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-1.5">
            <span className={cn(
              "h-2 w-2 rounded-full animate-pulse",
              showVisionPanel 
                ? isScenario2 ? "bg-destructive" 
                  : isScenario3 ? "bg-blue-500" 
                  : isScenario4 ? "bg-orange-500"
                  : "bg-destructive"
                : "bg-success"
            )} />
            <span className="text-sm font-mono">LIVE</span>
          </div>
        </div>
      </div>

      {/* Signal Summary Cards */}
      <SignalSummary />

      {/* Main Grid: Unified layout with smooth transitions */}
      <div className={cn(
        "grid gap-6 transition-all duration-700 ease-in-out",
        showVisionPanel 
          ? "lg:grid-cols-4" // Vision: [1 Telemetry] [2 Video] [1 Reliability]
          : showScenario1DecisionPanel
          ? "lg:grid-cols-4" // Scenario 1: [1 Telemetry] [2 Decision] [1 Reliability]
          : "lg:grid-cols-3"  // Normal: [2 Telemetry] [1 Reliability]
      )}>
        {/* Telemetry Grid - expands/shrinks smoothly */}
        <div className={cn(
          "transition-all duration-700 ease-in-out",
          (showVisionPanel || showScenario1DecisionPanel) ? "lg:col-span-1" : "lg:col-span-2"
        )}>
          <TelemetryGrid compact={(showVisionPanel || showScenario1DecisionPanel) ?? undefined} />
        </div>
        
        {/* Video Panel - slides in/out (for vision scenarios) */}
        <div className={cn(
          "lg:col-span-2 transition-all duration-700 ease-in-out overflow-hidden",
          showVisionPanel 
            ? "opacity-100 max-h-[800px] translate-x-0" 
            : "opacity-0 max-h-0 -translate-x-full absolute pointer-events-none"
        )}>
          <Scenario2VideoPanel 
            events={events}
            currentTimeSec={simState?.current_time_sec ?? 0}
            scenario={activeScenario ?? "scenario2"}
          />
        </div>
        
        {/* Decision Panel - slides in/out (for Scenario 1) */}
        <div className={cn(
          "lg:col-span-2 transition-all duration-700 ease-in-out overflow-hidden",
          showScenario1DecisionPanel 
            ? "opacity-100 max-h-[800px] translate-x-0" 
            : "opacity-0 max-h-0 -translate-x-full absolute pointer-events-none"
        )}>
          <Scenario1DecisionPanel
            decisions={decisions}
            onSubmitDecision={handleSubmitDecision}
            currentTimeSec={simState?.current_time_sec ?? 0}
          />
        </div>
        
        {/* Source Reliability with Decision Overlay */}
        <div className="relative transition-all duration-700 ease-in-out">
          <SourceReliability />
          {/* Decision cards overlay on top - for vision scenarios */}
          {showVisionPanel && decisions.length > 0 && (
            <Scenario2DecisionOverlay
              decisions={decisions}
              onSubmitDecision={handleSubmitDecision}
            />
          )}
        </div>
      </div>
    </div>
  )
}
