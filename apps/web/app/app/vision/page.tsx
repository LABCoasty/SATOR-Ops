"use client"

import { useState, useCallback } from "react"
import { Video, AlertCircle, Eye } from "lucide-react"
import { VisionStatus } from "@/components/app/vision/vision-status"
import { SafetyEventsPanel } from "@/components/app/vision/safety-events-panel"
import { IncidentList } from "@/components/app/vision/incident-list"
import { VideoInput } from "@/components/app/vision/video-input"
import { DecisionCard } from "@/components/decision-card/DecisionCard"
import { useDecisionCard, useIncident } from "@/hooks/use-incidents"
import { Badge } from "@/components/ui/badge"
import type { OvershootFrame } from "@/lib/overshoot-client"

export default function VisionPage() {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null)
  const [lastFrame, setLastFrame] = useState<OvershootFrame | null>(null)

  const handleFrame = useCallback((frame: OvershootFrame) => {
    setLastFrame(frame)
  }, [])
  
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Video className="h-6 w-6" />
            Vision Monitoring
          </h1>
          <p className="text-sm text-muted-foreground">
            Live video analysis with Overshoot.ai + LeanMCP processing
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-primary/50 bg-primary/10 px-3 py-1.5">
          <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
          <span className="text-sm font-mono text-primary">SCENARIO 2</span>
        </div>
      </div>

      {/* Video Input + Vision Status */}
      <div className="grid gap-6 lg:grid-cols-2">
        <VideoInput onFrame={handleFrame} />
        <VisionStatus />
      </div>

      {/* Main Grid: Incidents + Decision Card + Safety Events */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: Incident List */}
        <div className="lg:col-span-1">
          <IncidentList 
            onSelectIncident={setSelectedIncidentId}
            selectedIncidentId={selectedIncidentId ?? undefined}
          />
        </div>

        {/* Center: Decision Card or Empty State */}
        <div className="lg:col-span-1">
          {selectedIncidentId ? (
            <SelectedIncidentCard incidentId={selectedIncidentId} />
          ) : (
            <div className="rounded-lg border border-dashed border-border bg-card p-8 h-full flex flex-col items-center justify-center text-center">
              <Eye className="h-12 w-12 text-muted-foreground/30 mb-4" />
              <h3 className="font-medium text-muted-foreground">No Incident Selected</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Select an incident from the list to view its decision card
              </p>
            </div>
          )}
        </div>

        {/* Right: Safety Events */}
        <div className="lg:col-span-1">
          <SafetyEventsPanel events={lastFrame?.safety_events} />
        </div>
      </div>
    </div>
  )
}

// Sub-component to handle selected incident card
function SelectedIncidentCard({ incidentId }: { incidentId: string }) {
  const { incident, acknowledgeIncident, resolveIncident } = useIncident(incidentId)
  const { card, submitAction, answerQuestion } = useDecisionCard(incidentId)

  if (!incident) {
    return (
      <div className="rounded-lg border border-border bg-card p-6 flex items-center justify-center">
        <span className="text-muted-foreground">Loading incident...</span>
      </div>
    )
  }

  // If no decision card exists yet, show incident summary
  if (!card) {
    return (
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-warning" />
            <h2 className="font-semibold">Incident Details</h2>
          </div>
        </div>
        <div className="p-4 space-y-4">
          <div>
            <Badge variant={
              incident.severity === "emergency" ? "destructive" :
              incident.severity === "critical" ? "destructive" :
              incident.severity === "warning" ? "secondary" : "outline"
            }>
              {incident.severity.toUpperCase()}
            </Badge>
          </div>
          <h3 className="font-medium">{incident.title}</h3>
          <p className="text-sm text-muted-foreground">{incident.description}</p>
          <div className="text-xs text-muted-foreground">
            <p>State: {incident.state}</p>
            <p>Created: {new Date(incident.created_at).toLocaleString()}</p>
            {incident.contradiction_ids.length > 0 && (
              <p>Contradictions: {incident.contradiction_ids.length}</p>
            )}
          </div>
          {incident.state === "open" && (
            <button
              onClick={() => acknowledgeIncident("operator_ui")}
              className="w-full mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              Acknowledge Incident
            </button>
          )}
        </div>
      </div>
    )
  }

  // Show full decision card
  return (
    <DecisionCard
      cardId={card.card_id}
      incidentId={card.incident_id}
      title={card.title}
      summary={card.summary}
      severity={card.severity as "info" | "warning" | "critical" | "emergency"}
      trustScore={card.trust_score}
      reasonCodes={card.reason_codes}
      predictions={card.predictions}
      contradictions={card.contradictions}
      allowedActions={card.allowed_actions}
      recommendedActionId={card.recommended_action_id}
      recommendationRationale={card.recommendation_rationale}
      questions={card.questions}
      expiresAt={card.expires_at}
      onActionSelect={(actionId) => {
        submitAction(actionId, "Action taken via Vision UI")
      }}
      onQuestionAnswer={(questionId, answer) => {
        answerQuestion(questionId, answer)
      }}
      onViewReceipt={() => {
        window.location.href = `/app/receipt?incident=${incidentId}`
      }}
      onViewAudit={() => {
        window.open(`/audit/log?incident=${incidentId}`, '_blank')
      }}
    />
  )
}
