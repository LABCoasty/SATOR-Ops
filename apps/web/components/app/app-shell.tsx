"use client"

import type React from "react"
import { useState, useCallback, useEffect, useRef } from "react"
import { AppSidebar } from "./app-sidebar"
import { AppTopBar } from "./app-top-bar"
import { AgentButton } from "./agent-button"
import { DecisionPrompt, EventToast, type DecisionPromptData } from "./decision-prompt"
import { ScenarioCompleteModal } from "./scenario-complete-modal"
import { useSimulationContext, type SimulationEvent } from "@/contexts/simulation-context"
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

export function AppShell({ children }: { children: React.ReactNode }) {
  // Enhanced simulation state from context
  const {
    state: simState,
    events,
    decisions,
    completedDecisions,
    activeScenario,
    isRunning,
    isLoading: simLoading,
    startSimulation,
    submitDecision
  } = useSimulationContext()

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
    await submitDecision(decisionId, response)
  }, [submitDecision])

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
  const isScenario2 = activeScenario === "scenario2"
  const isScenario3 = activeScenario === "scenario3"
  const isScenario4 = activeScenario === "scenario4"
  const isVisionScenario = isScenario2 || isScenario3 || isScenario4

  // Get current decision to show (first pending decision) - only for scenario 1
  const currentDecision = !isVisionScenario && decisions.length > 0 ? decisions[0] : null

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
        {isRunning && simState && (
          <div className="border-b border-border bg-card px-4 py-2">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium">
                  {simState.phase === "monitoring" && "Monitoring..."}
                  {simState.phase === "alert" && "Alert Active"}
                  {simState.phase === "decision" && "Decision Required"}
                  {simState.phase === "resolution" && "Resolving..."}
                </span>
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    simState.phase === "monitoring" && "bg-success animate-pulse",
                    simState.phase === "alert" && "bg-warning animate-pulse",
                    simState.phase === "decision" && "bg-destructive animate-pulse",
                    simState.phase === "resolution" && "bg-primary"
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
