"use client"

import type React from "react"
import { useState, useCallback, useEffect, useRef } from "react"
import { AppSidebar } from "./app-sidebar"
import { AppTopBar } from "./app-top-bar"
import { AgentButton } from "./agent-button"
import { VideoAlertModal, type Scenario2Result } from "./vision/video-alert-modal"
import { DecisionPrompt, EventToast, type DecisionPromptData } from "./decision-prompt"
import { useSimulationContext, type SimulationEvent } from "@/contexts/simulation-context"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

export type AppMode = "ingest" | "decision" | "artifact"

// YouTube video URL for Scenario 2 video modal
const YOUTUBE_VIDEO_ID = "IPpKZx854VQ"
const YOUTUBE_EMBED_URL = `https://www.youtube.com/embed/${YOUTUBE_VIDEO_ID}`

export function AppShell({ children }: { children: React.ReactNode }) {
  // Enhanced simulation state from context
  const {
    state: simState,
    events,
    decisions,
    isRunning,
    isLoading: simLoading,
    startSimulation,
    submitDecision
  } = useSimulationContext()

  // Event toast state
  const [currentEventToast, setCurrentEventToast] = useState<SimulationEvent | null>(null)
  const lastShownEventRef = useRef<string | null>(null)

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

  // Handle decision submission
  const handleDecisionSubmit = useCallback(async (decisionId: string, response: string) => {
    await submitDecision(decisionId, response)
  }, [submitDecision])

  // Handle scenario 1 start (enhanced)
  const handleScenario1 = useCallback(async () => {
    await startSimulation("scenario1")
  }, [startSimulation])

  // Scenario 2 video modal state (kept for legacy video alert support)
  const [scenario2ModalOpen, setScenario2ModalOpen] = useState(false)
  const [scenario2Processing] = useState(false)
  const [scenario2Progress] = useState(0)
  const [scenario2Message] = useState("")
  const [scenario2Result] = useState<Scenario2Result | null>(null)

  const handleScenario2 = useCallback(async () => {
    // Start the enhanced simulation for scenario 2
    await startSimulation("scenario2")
  }, [startSimulation])

  // Get current decision to show (first pending decision)
  const currentDecision = decisions.length > 0 ? decisions[0] : null

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
          scenario1Loading={simLoading && !simState}
          scenario2Loading={simLoading || scenario2Processing}
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

      {/* Event Toast */}
      {currentEventToast && (
        <EventToast
          event={currentEventToast}
          onClose={() => setCurrentEventToast(null)}
        />
      )}

      {/* Scenario 2 Video Alert Modal - Only shown after processing completes */}
      <VideoAlertModal
        open={scenario2ModalOpen && !scenario2Processing}
        onOpenChange={setScenario2ModalOpen}
        processing={false}
        progress={scenario2Progress}
        progressMessage={scenario2Message}
        result={scenario2Result}
        videoUrl={YOUTUBE_EMBED_URL}
      />
    </div>
  )
}
