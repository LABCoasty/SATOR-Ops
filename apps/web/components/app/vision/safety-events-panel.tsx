"use client"

import { AlertTriangle, Shield, Check, Clock, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { useVisionLatest, type SafetyEvent } from "@/hooks/use-vision"

const severityConfig = {
  info: { color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/30" },
  warning: { color: "text-yellow-500", bg: "bg-yellow-500/10", border: "border-yellow-500/30" },
  critical: { color: "text-orange-500", bg: "bg-orange-500/10", border: "border-orange-500/30" },
  emergency: { color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/30" },
}

interface SafetyEventsPanelProps {
  events?: SafetyEvent[]
  className?: string
}

export function SafetyEventsPanel({ events: propEvents, className }: SafetyEventsPanelProps) {
  const { frame, loading } = useVisionLatest()
  
  // Use prop events if provided, otherwise use from latest frame
  const events = propEvents ?? frame?.safety_events ?? []

  if (loading) {
    return (
      <div className={cn("rounded-lg border border-border bg-card p-6 flex items-center justify-center", className)}>
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className={cn("rounded-lg border border-border bg-card", className)}>
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-warning" />
            <h2 className="font-semibold">Safety Events</h2>
          </div>
          <Badge 
            variant={events.length > 0 ? "destructive" : "secondary"} 
            className="text-xs"
          >
            {events.length} active
          </Badge>
        </div>
      </div>

      {/* Events List */}
      <div className="divide-y divide-border max-h-[400px] overflow-y-auto">
        {events.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <Check className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No active safety events</p>
            <p className="text-xs text-muted-foreground mt-1">System operating normally</p>
          </div>
        ) : (
          events.map((event) => {
            const config = severityConfig[event.severity] ?? severityConfig.warning
            
            return (
              <div 
                key={event.event_id}
                className={cn(
                  "px-4 py-3 transition-colors hover:bg-muted/50",
                  config.bg
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className={cn("h-4 w-4 mt-0.5", config.color)} />
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge 
                          variant="outline" 
                          className={cn("text-xs", config.border, config.color)}
                        >
                          {event.event_type}
                        </Badge>
                        <Badge 
                          variant={event.severity === "emergency" ? "destructive" : "secondary"}
                          className="text-xs"
                        >
                          {event.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium">{event.description}</p>
                      {event.visual_evidence && (
                        <p className="text-xs text-muted-foreground">
                          {event.visual_evidence}
                        </p>
                      )}
                      {event.related_equipment.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {event.related_equipment.map((eq) => (
                            <span key={eq} className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                              {eq}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs text-muted-foreground">
                      {Math.round(event.confidence * 100)}%
                    </span>
                    <div className="flex items-center gap-1 mt-1">
                      {event.acknowledged ? (
                        <Badge variant="outline" className="text-xs">Acked</Badge>
                      ) : (
                        <Badge variant="destructive" className="text-xs">New</Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
