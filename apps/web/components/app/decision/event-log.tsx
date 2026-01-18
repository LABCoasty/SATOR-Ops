"use client"

import { useState } from "react"
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  Clock, 
  Filter,
  ChevronDown,
  ChevronUp
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useOptionalSimulationContext, type SimulationEvent } from "@/contexts/simulation-context"

type SeverityFilter = "all" | "info" | "warning" | "critical"

export function EventLog() {
  const simulation = useOptionalSimulationContext()
  const [filter, setFilter] = useState<SeverityFilter>("all")
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const events = simulation?.events || []
  
  const filteredEvents = filter === "all" 
    ? events 
    : events.filter(e => e.severity === filter)

  // Sort by time (most recent first)
  const sortedEvents = [...filteredEvents].sort((a, b) => b.time_sec - a.time_sec)

  const getIcon = (severity: string, requiresDecision: boolean) => {
    if (requiresDecision) {
      return <AlertTriangle className="h-4 w-4 text-warning" />
    }
    switch (severity) {
      case "critical":
        return <AlertTriangle className="h-4 w-4 text-destructive" />
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-warning" />
      default:
        return <Info className="h-4 w-4 text-primary" />
    }
  }

  const getStatusColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-destructive"
      case "warning":
        return "bg-warning"
      default:
        return "bg-primary"
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-primary" />
            <div>
              <h2 className="font-semibold">Event Log</h2>
              <p className="text-xs text-muted-foreground">
                {events.length} event(s) captured
              </p>
            </div>
          </div>
          
          {/* Filter Buttons */}
          <div className="flex items-center gap-1">
            <Button
              variant={filter === "all" ? "default" : "ghost"}
              size="sm"
              onClick={() => setFilter("all")}
              className="h-7 px-2 text-xs"
            >
              All
            </Button>
            <Button
              variant={filter === "info" ? "default" : "ghost"}
              size="sm"
              onClick={() => setFilter("info")}
              className="h-7 px-2 text-xs"
            >
              Info
            </Button>
            <Button
              variant={filter === "warning" ? "default" : "ghost"}
              size="sm"
              onClick={() => setFilter("warning")}
              className="h-7 px-2 text-xs"
            >
              Warning
            </Button>
            <Button
              variant={filter === "critical" ? "default" : "ghost"}
              size="sm"
              onClick={() => setFilter("critical")}
              className="h-7 px-2 text-xs"
            >
              Critical
            </Button>
          </div>
        </div>
      </div>

      {sortedEvents.length === 0 ? (
        <div className="p-8 text-center">
          <Activity className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            {simulation?.isRunning 
              ? "Waiting for events..." 
              : "Start a simulation to capture events"}
          </p>
        </div>
      ) : (
        <div className="max-h-[400px] overflow-y-auto">
          <div className="divide-y divide-border">
            {sortedEvents.map((event) => (
              <div key={event.event_id} className="px-4 py-3">
                <button
                  onClick={() => setExpandedId(expandedId === event.event_id ? null : event.event_id)}
                  className="w-full text-left"
                >
                  <div className="flex items-start gap-3">
                    {/* Timeline indicator */}
                    <div className="flex flex-col items-center">
                      <div className={cn(
                        "h-2 w-2 rounded-full",
                        getStatusColor(event.severity)
                      )} />
                      <div className="w-px h-full bg-border mt-1" />
                    </div>

                    {/* Event content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          {getIcon(event.severity, event.requires_decision)}
                          <span className="font-medium text-sm truncate">{event.title}</span>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-xs text-muted-foreground font-mono">
                            {event.time_sec.toFixed(1)}s
                          </span>
                          {expandedId === event.event_id ? (
                            <ChevronUp className="h-3 w-3 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="h-3 w-3 text-muted-foreground" />
                          )}
                        </div>
                      </div>

                      {/* Tags */}
                      <div className="flex items-center gap-2 mt-1">
                        <span className={cn(
                          "px-1.5 py-0.5 rounded text-[10px] font-medium uppercase",
                          event.severity === "critical" && "bg-destructive/20 text-destructive",
                          event.severity === "warning" && "bg-warning/20 text-warning",
                          event.severity === "info" && "bg-primary/20 text-primary"
                        )}>
                          {event.severity}
                        </span>
                        {event.requires_decision && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-medium uppercase bg-accent/20 text-accent">
                            Decision Required
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </button>

                {/* Expanded details */}
                {expandedId === event.event_id && (
                  <div className="mt-3 ml-5 rounded-md bg-muted/50 p-3">
                    <p className="text-sm text-muted-foreground">{event.description}</p>
                    {event.timestamp && (
                      <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Captured at {new Date(event.timestamp).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Footer */}
      {events.length > 0 && (
        <div className="border-t border-border px-4 py-2 bg-muted/30">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-primary" />
                {events.filter(e => e.severity === "info").length} Info
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-warning" />
                {events.filter(e => e.severity === "warning").length} Warning
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-destructive" />
                {events.filter(e => e.severity === "critical").length} Critical
              </span>
            </div>
            <span>
              {events.filter(e => e.requires_decision).length} decisions required
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
