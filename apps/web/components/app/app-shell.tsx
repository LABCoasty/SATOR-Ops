"use client"

import type React from "react"
import { useState, useCallback, useEffect, useRef } from "react"
import { AppSidebar } from "./app-sidebar"
import { AppTopBar } from "./app-top-bar"
import { AgentButton } from "./agent-button"
import { DecisionPrompt, EventToast, type DecisionPromptData } from "./decision-prompt"
import { ScenarioCompleteModal } from "./scenario-complete-modal"
import { useSimulationContext, type SimulationEvent } from "@/contexts/simulation-context"
import { useVoiceCallContext } from "@/contexts/voice-call-context"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

export type AppMode = "ingest" | "decision" | "artifact"

// Scenario name mapping
const SCENARIO_NAMES: Record<string, string> = {
  scenario1: "Valve Incident",
  scenario2: "Oil Rig Analysis",
  scenario3: "Water Pipe Leakage",
  scenario4: "Data Center Arc Flash",
}

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

export function AppShell({ children }: { children: React.ReactNode }) {
  // Enhanced simulation state from context
  const {
    state: simState,
    events,
    decisions,
    completedDecisions,
    activeScenario,
    isRunning,
    isPaused,
    isLoading: simLoading,
    startSimulation,
    submitDecision
  } = useSimulationContext()

  // Voice call context for escalation
  const { triggerCall } = useVoiceCallContext()

  // Event toast state
  const [currentEventToast, setCurrentEventToast] = useState<SimulationEvent | null>(null)
  const lastShownEventRef = useRef<string | null>(null)
  
  // Scenario completion modal state
  const [showCompletionModal, setShowCompletionModal] = useState(false)
  const [completedScenarioData, setCompletedScenarioData] = useState<{
    scenarioId: string
    scenarioName: string
    trustScore: number
    decisionsCount: number
    eventsCount: number
    duration: number
  } | null>(null)
  const prevRunningRef = useRef(false)

  // Show event toasts for new events (non-decision events)
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1]
      if (
        latestEvent.event_id !== lastShownEventRef.current &&
        !latestEvent.requires_decision
      ) {
        lastShownEventRef.current = latestEvent.event_id
        setCurrentEventToast(latestEvent)
      }
    }
  }, [events])

  // Detect simulation completion and show modal
  useEffect(() => {
    // Check if simulation just completed (was running, now not running)
    if (prevRunningRef.current && !isRunning && simState && activeScenario) {
      // Simulation completed
      setCompletedScenarioData({
        scenarioId: activeScenario,
        scenarioName: SCENARIO_NAMES[activeScenario] || activeScenario,
        trustScore: simState.trust_score,
        decisionsCount: simState.decisions_made,
        eventsCount: simState.events_triggered,
        duration: simState.current_time_sec,
      })
      setShowCompletionModal(true)
    }
    prevRunningRef.current = isRunning
  }, [isRunning, simState, activeScenario])

  // Handle decision submission
  const handleDecisionSubmit = useCallback(async (decisionId: string, response: string) => {
    // Find the decision to get its details for context
    const decision = decisions.find(d => d.decision_id === decisionId)
    
    // Submit the decision first
    await submitDecision(decisionId, response)
    
    // If this is an escalation to supervisor, trigger the voice call
    if (isEscalationToSupervisor(response)) {
      triggerCall({
        currentPage: '/app/ingest',
        trustScore: simState?.trust_score,
        trustState: simState?.trust_score !== undefined 
          ? (simState.trust_score >= 0.8 ? 'high' : simState.trust_score >= 0.6 ? 'medium' : 'low')
          : undefined,
        scenarioName: activeScenario ? SCENARIO_NAMES[activeScenario] : undefined,
        decisionId: decisionId,
        decisionTitle: decision?.title,
        escalationType: response,
      })
    }
  }, [submitDecision, decisions, simState?.trust_score, activeScenario, triggerCall])

  // Handle scenario 1 start (enhanced)
  const handleScenario1 = useCallback(async () => {
    await startSimulation("scenario1")
  }, [startSimulation])

  const handleScenario2 = useCallback(async () => {
    await startSimulation("scenario2")
  }, [startSimulation])

  const handleScenario3 = useCallback(async () => {
    await startSimulation("scenario3")
  }, [startSimulation])

  const handleScenario4 = useCallback(async () => {
    await startSimulation("scenario4")
  }, [startSimulation])

  // Scenario 2, 3 & 4 handle their own decisions in the ingest page
  // Scenario 1 also handles decisions in the ingest page now (centered panel)
  const isScenario2 = activeScenario === "scenario2"
  const isScenario3 = activeScenario === "scenario3"
  const isScenario4 = activeScenario === "scenario4"
  const isVisionScenario = isScenario2 || isScenario3 || isScenario4
  const isScenario1 = activeScenario === "scenario1"

  // Get current decision to show (first pending decision) - only show floating modal for non-scenario cases
  // Scenarios 1-4 all handle decisions in their respective ingest pages
  const currentDecision = !isScenario1 && !isVisionScenario && decisions.length > 0 ? decisions[0] : null

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Left Sidebar Navigation */}
      <AppSidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Status Bar */}
        <AppTopBar
          onScenario1={handleScenario1}
          onScenario2={handleScenario2}
          onScenario3={handleScenario3}
          onScenario4={handleScenario4}
          scenario1Loading={simLoading && !simState}
          scenario2Loading={simLoading && isScenario2}
          scenario3Loading={simLoading && isScenario3}
          scenario4Loading={simLoading && isScenario4}
        />

        {/* Simulation Progress Bar */}
        {(isRunning || isPaused) && simState && (
          <div className={cn(
            "border-b border-border bg-card px-4 py-2",
            isPaused && "bg-blue-500/10 border-blue-500/30"
          )}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium">
                  {isPaused && "📞 Supervisor Call - Scenario Paused"}
                  {!isPaused && simState.phase === "monitoring" && "Monitoring..."}
                  {!isPaused && simState.phase === "alert" && "Alert Active"}
                  {!isPaused && simState.phase === "decision" && "Decision Required"}
                  {!isPaused && simState.phase === "resolution" && "Resolving..."}
                  {!isPaused && simState.phase === "escalated" && "Escalated to Supervisor"}
                </span>
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    isPaused && "bg-blue-500 animate-pulse",
                    !isPaused && simState.phase === "monitoring" && "bg-success animate-pulse",
                    !isPaused && simState.phase === "alert" && "bg-warning animate-pulse",
                    !isPaused && simState.phase === "decision" && "bg-destructive animate-pulse",
                    !isPaused && simState.phase === "resolution" && "bg-primary",
                    !isPaused && simState.phase === "escalated" && "bg-blue-500 animate-pulse"
                  )}
                />
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span>Time: {simState.current_time_sec.toFixed(0)}s / {simState.total_duration_sec}s</span>
                <span>Trust: <span className={cn(
                  "font-mono font-medium",
                  simState.trust_score >= 0.8 && "text-success",
                  simState.trust_score >= 0.6 && simState.trust_score < 0.8 && "text-warning",
                  simState.trust_score < 0.6 && "text-destructive"
                )}>{(simState.trust_score * 100).toFixed(0)}%</span></span>
                <span>Events: {simState.events_triggered}</span>
                <span>Decisions: {simState.decisions_made}</span>
              </div>
            </div>
            <Progress value={simState.progress_percent} className="h-1" />
          </div>
        )}

        {/* Main Canvas with Agent Popup */}
        <div className="flex flex-1 overflow-hidden relative">
          <main className="flex-1 overflow-auto p-6">{children}</main>

          {/* Agent Popup Button */}
          <AgentButton />
        </div>
      </div>

      {/* Decision Prompt Modal */}
      {currentDecision && (
        <DecisionPrompt
          decision={currentDecision as DecisionPromptData}
          onSubmit={handleDecisionSubmit}
        />
      )}

      {/* Event Toast - hide for vision scenarios (handled in ingest page) */}
      {currentEventToast && !isVisionScenario && (
        <EventToast
          event={currentEventToast}
          onClose={() => setCurrentEventToast(null)}
        />
      )}

      {/* Scenario Completion Modal */}
      {showCompletionModal && completedScenarioData && (
        <ScenarioCompleteModal
          scenarioId={completedScenarioData.scenarioId}
          scenarioName={completedScenarioData.scenarioName}
          trustScore={completedScenarioData.trustScore}
          decisionsCount={completedScenarioData.decisionsCount}
          eventsCount={completedScenarioData.eventsCount}
          duration={completedScenarioData.duration}
          onClose={() => {
            setShowCompletionModal(false)
            setCompletedScenarioData(null)
          }}
          onAnchor={() => {
            // Anchor was successful
          }}
        />
      )}
    </div>
  )
}
