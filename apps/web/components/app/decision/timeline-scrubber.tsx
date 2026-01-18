"use client"

import { useState, useEffect, useMemo } from "react"
import { ChevronLeft, ChevronRight, Play, Pause, FileText, Loader2, Activity, List } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { useTimeline } from "@/hooks/use-decisions"
import { useOptionalSimulationContext } from "@/contexts/simulation-context"

interface TimelineEvent {
  id: string
  time: string
  time_sec: number
  label: string
  trust_score: number
  has_contradiction: boolean
  description?: string
  severity?: string
  requires_decision?: boolean
  type: "api" | "simulation" | "decision"
}

export function TimelineScrubber() {
  const { events: apiEvents, loading, error } = useTimeline()
  const simulation = useOptionalSimulationContext()
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [showAllEvents, setShowAllEvents] = useState(true)

  // Convert API events to timeline format
  const apiTimelineEvents: TimelineEvent[] = useMemo(() => {
    return apiEvents.map((event, idx) => ({
      id: `api-${idx}`,
      time: event.time,
      time_sec: event.timestamp || idx * 10,
      label: event.label,
      trust_score: event.trust_score,
      has_contradiction: event.has_contradiction,
      description: event.description,
      type: "api" as const
    }))
  }, [apiEvents])

  // Convert simulation events to timeline format
  const simulationTimelineEvents: TimelineEvent[] = useMemo(() => {
    if (!simulation?.events || simulation.events.length === 0) {
      return []
    }

    return simulation.events.map(event => ({
      id: event.event_id,
      time: formatTime(event.time_sec),
      time_sec: event.time_sec,
      label: event.severity === "critical" ? "Critical Event" : 
             event.severity === "warning" ? "Warning" : "Info",
      trust_score: simulation.state?.trust_score || 0.95,
      has_contradiction: event.severity === "critical" || event.severity === "warning",
      description: `${event.title}: ${event.description}`,
      severity: event.severity,
      requires_decision: event.requires_decision,
      type: "simulation" as const
    }))
  }, [simulation?.events, simulation?.state?.trust_score])

  // Convert completed decisions to timeline format
  const decisionTimelineEvents: TimelineEvent[] = useMemo(() => {
    if (!simulation?.completedDecisions || simulation.completedDecisions.length === 0) {
      return []
    }

    return simulation.completedDecisions.map(decision => ({
      id: `decision-${decision.decision_id}`,
      time: formatTime(decision.time_sec),
      time_sec: decision.time_sec,
      label: "Operator Decision",
      trust_score: simulation.state?.trust_score || 0.95,
      has_contradiction: false,
      description: `${decision.title}: Responded with "${decision.response}"${decision.explanation ? ` - ${decision.explanation}` : ""}`,
      severity: decision.severity,
      requires_decision: false,
      type: "decision" as const
    }))
  }, [simulation?.completedDecisions, simulation?.state?.trust_score])

  // Combine all events when simulation is running
  const allEvents = useMemo(() => {
    if (simulation?.isRunning || (simulation?.events && simulation.events.length > 0)) {
      // Merge simulation events and decisions, sorted by time
      const combined = [...simulationTimelineEvents, ...decisionTimelineEvents]
        .sort((a, b) => a.time_sec - b.time_sec)
      return combined.length > 0 ? combined : apiTimelineEvents
    }
    return apiTimelineEvents
  }, [simulation?.isRunning, simulation?.events, simulationTimelineEvents, decisionTimelineEvents, apiTimelineEvents])

  // Auto-select latest event when new events arrive during simulation
  useEffect(() => {
    if (simulation?.isRunning && allEvents.length > 0) {
      setSelectedIndex(allEvents.length - 1)
    }
  }, [simulation?.isRunning, allEvents.length])

  // Auto-play functionality
  useEffect(() => {
    if (!isPlaying || allEvents.length === 0) return

    const interval = setInterval(() => {
      setSelectedIndex(prev => {
        if (prev >= allEvents.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 1500)

    return () => clearInterval(interval)
  }, [isPlaying, allEvents.length])

  if (loading && !simulation?.isRunning) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading timeline...</span>
      </div>
    )
  }

  if ((error || allEvents.length === 0) && !simulation?.isRunning) {
    return (
      <div className="rounded-lg border border-border bg-card p-4">
        <p className="text-center text-muted-foreground">No timeline events available. Start a simulation to capture events.</p>
      </div>
    )
  }

  const selectedEvent = allEvents[Math.min(selectedIndex, allEvents.length - 1)]
  
  // For display, limit markers but show all in list
  const displayMarkers = allEvents.length > 20 
    ? allEvents.filter((_, i) => i % Math.ceil(allEvents.length / 20) === 0 || i === allEvents.length - 1)
    : allEvents

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold">Event Timeline</h3>
          <span className="text-xs text-muted-foreground">
            {allEvents.length} event(s) captured
          </span>
          {simulation?.isRunning && (
            <span className="flex items-center gap-1 text-xs text-primary">
              <Activity className="h-3 w-3 animate-pulse" />
              Live capture
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={showAllEvents ? "default" : "outline"}
            size="sm"
            className="h-8 gap-1 text-xs"
            onClick={() => setShowAllEvents(!showAllEvents)}
          >
            <List className="h-3 w-3" />
            {showAllEvents ? "Hide List" : "Show All"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8 w-8 p-0 bg-transparent"
            onClick={() => setSelectedIndex(Math.max(0, selectedIndex - 1))}
            disabled={selectedIndex === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8 w-8 p-0 bg-transparent"
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8 w-8 p-0 bg-transparent"
            onClick={() => setSelectedIndex(Math.min(allEvents.length - 1, selectedIndex + 1))}
            disabled={selectedIndex === allEvents.length - 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Timeline Track */}
      <div className="relative">
        {/* Background track */}
        <div className="h-2 rounded-full bg-muted" />

        {/* Progress indicator for simulation */}
        {simulation?.isRunning && simulation.state && (
          <div 
            className="absolute top-0 left-0 h-2 rounded-full bg-primary/30 transition-all duration-300"
            style={{ width: `${simulation.state.progress_percent}%` }}
          />
        )}

        {/* Event markers */}
        <div className="absolute inset-0 flex items-center justify-between px-1">
          {displayMarkers.map((event, index) => {
            const actualIndex = allEvents.findIndex(e => e.id === event.id)
            return (
              <button
                key={event.id}
                onClick={() => setSelectedIndex(actualIndex)}
                className={cn(
                  "relative h-4 w-4 rounded-full border-2 transition-all",
                  actualIndex === selectedIndex
                    ? "border-primary bg-primary scale-125"
                    : event.type === "decision"
                      ? "border-accent bg-accent/50 hover:scale-110"
                      : event.has_contradiction
                        ? "border-warning bg-warning/50 hover:scale-110"
                        : "border-muted-foreground bg-muted hover:scale-110 hover:border-foreground",
                )}
              >
                {event.has_contradiction && actualIndex !== selectedIndex && (
                  <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-warning" />
                )}
                {event.requires_decision && actualIndex !== selectedIndex && (
                  <span className="absolute -bottom-1 -right-1 h-2 w-2 rounded-full bg-accent animate-pulse" />
                )}
                {event.type === "decision" && actualIndex !== selectedIndex && (
                  <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-success" />
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* All Events List (expandable) */}
      {showAllEvents && allEvents.length > 0 && (
        <div className="border rounded-md max-h-48 overflow-y-auto bg-muted/30">
          <div className="divide-y divide-border">
            {allEvents.map((event, index) => (
              <button
                key={event.id}
                onClick={() => setSelectedIndex(index)}
                className={cn(
                  "w-full text-left px-3 py-2 text-sm transition-colors hover:bg-muted/50",
                  index === selectedIndex && "bg-primary/10"
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "h-2 w-2 rounded-full flex-shrink-0",
                      event.type === "decision" ? "bg-success" :
                      event.severity === "critical" ? "bg-destructive" :
                      event.severity === "warning" ? "bg-warning" : "bg-primary"
                    )} />
                    <span className="font-mono text-xs text-muted-foreground">{event.time}</span>
                    <span className="truncate">{event.description?.split(":")[0] || event.label}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {event.type === "decision" && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-success/20 text-success uppercase">Decision</span>
                    )}
                    {event.requires_decision && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent/20 text-accent uppercase">Action</span>
                    )}
                    <span className={cn(
                      "font-mono text-xs",
                      event.trust_score >= 0.85 ? "text-success" :
                      event.trust_score >= 0.7 ? "text-warning" : "text-destructive"
                    )}>
                      {event.trust_score.toFixed(2)}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Selected Event Details */}
      {selectedEvent && (
        <>
          <div className="flex items-center justify-between rounded-md bg-muted/50 p-3">
            <div className="flex items-center gap-4">
              <div>
                <span className="font-mono text-lg font-bold">{selectedEvent.time}</span>
                <p className="text-sm text-muted-foreground">{selectedEvent.label}</p>
              </div>
              {selectedEvent.type === "decision" && (
                <span className="rounded-md bg-success/20 px-2 py-1 text-xs font-medium text-success">
                  Operator Decision Made
                </span>
              )}
              {selectedEvent.has_contradiction && selectedEvent.type !== "decision" && (
                <span className={cn(
                  "rounded-md px-2 py-1 text-xs font-medium",
                  selectedEvent.severity === "critical" 
                    ? "bg-destructive/20 text-destructive"
                    : "bg-warning/20 text-warning"
                )}>
                  {selectedEvent.severity === "critical" ? "Critical event" : "Warning detected"}
                </span>
              )}
              {selectedEvent.requires_decision && (
                <span className="rounded-md bg-accent/20 px-2 py-1 text-xs font-medium text-accent">
                  Decision required
                </span>
              )}
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <span className="text-xs text-muted-foreground">Trust Score</span>
                <p
                  className={cn(
                    "font-mono text-lg font-bold",
                    selectedEvent.trust_score >= 0.85
                      ? "text-success"
                      : selectedEvent.trust_score >= 0.7
                        ? "text-warning"
                        : "text-destructive",
                  )}
                >
                  {selectedEvent.trust_score.toFixed(2)}
                </p>
              </div>
              <Button asChild variant="outline" size="sm" className="gap-2 bg-transparent">
                <Link href="/app/artifact">
                  <FileText className="h-4 w-4" />
                  View Linked Artifacts
                </Link>
              </Button>
            </div>
          </div>

          {/* Event Description */}
          {selectedEvent.description && (
            <p className="text-sm text-muted-foreground px-1">{selectedEvent.description}</p>
          )}
        </>
      )}

      {/* Summary Stats */}
      {allEvents.length > 0 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground border-t border-border pt-3">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-primary" />
              {allEvents.filter(e => e.type === "simulation" && e.severity === "info").length} Info
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-warning" />
              {allEvents.filter(e => e.severity === "warning").length} Warnings
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-destructive" />
              {allEvents.filter(e => e.severity === "critical").length} Critical
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-success" />
              {allEvents.filter(e => e.type === "decision").length} Decisions
            </span>
          </div>
          <span>
            Event {selectedIndex + 1} of {allEvents.length}
          </span>
        </div>
      )}
    </div>
  )
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 100)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${ms.toString().padStart(2, '0')}`
}
