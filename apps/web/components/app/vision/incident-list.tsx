"use client"

import { AlertCircle, Clock, CheckCircle, User, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { useActiveIncidents, type Incident } from "@/hooks/use-incidents"

const severityConfig = {
  info: { color: "status-context-text", bg: "status-context-dot", border: "status-context-border" },
  warning: { color: "status-uncertain-text", bg: "status-uncertain-dot", border: "status-uncertain-border" },
  critical: { color: "status-risk-text", bg: "status-risk-dot", border: "status-risk-border" },
  emergency: { color: "status-critical-text", bg: "status-critical-dot", border: "status-critical-border" },
}

const stateConfig = {
  open: { label: "Open", color: "status-critical-text", bg: "status-critical-bg" },
  acknowledged: { label: "Acknowledged", color: "status-uncertain-text", bg: "status-uncertain-bg" },
  resolved: { label: "Resolved", color: "status-verified-text", bg: "status-verified-bg" },
  closed: { label: "Closed", color: "text-muted-foreground", bg: "bg-muted" },
}

interface IncidentListProps {
  onSelectIncident?: (incidentId: string) => void
  selectedIncidentId?: string
  className?: string
}

export function IncidentList({ onSelectIncident, selectedIncidentId, className }: IncidentListProps) {
  const { incidents, loading, error } = useActiveIncidents()

  if (loading) {
    return (
      <div className={cn("rounded-lg border border-border bg-card p-6 flex items-center justify-center", className)}>
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading incidents...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn("rounded-lg border border-border bg-card p-6", className)}>
        <p className="text-sm text-destructive">Error: {error}</p>
      </div>
    )
  }

  return (
    <div className={cn("rounded-lg border border-border bg-card", className)}>
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-destructive" />
            <h2 className="font-semibold">Active Incidents</h2>
          </div>
          <Badge variant={incidents.length > 0 ? "destructive" : "secondary"}>
            {incidents.length}
          </Badge>
        </div>
      </div>

      {/* Incidents List */}
      <div className="divide-y divide-border max-h-[500px] overflow-y-auto">
        {incidents.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No active incidents</p>
            <p className="text-xs text-muted-foreground mt-1">All clear</p>
          </div>
        ) : (
          incidents.map((incident) => {
            const severity = severityConfig[incident.severity] ?? severityConfig.warning
            const state = stateConfig[incident.state] ?? stateConfig.open
            const isSelected = incident.incident_id === selectedIncidentId

            return (
              <button
                key={incident.incident_id}
                onClick={() => onSelectIncident?.(incident.incident_id)}
                className={cn(
                  "w-full px-4 py-3 text-left transition-colors hover:bg-muted/50",
                  isSelected && "bg-primary/5 border-l-2 border-l-primary"
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn("h-2 w-2 rounded-full", severity.bg)} />
                      <Badge 
                        variant="outline" 
                        className={cn("text-xs", severity.color, severity.border)}
                      >
                        {incident.severity.toUpperCase()}
                      </Badge>
                      <Badge 
                        variant="secondary" 
                        className={cn("text-xs", state.color, state.bg)}
                      >
                        {state.label}
                      </Badge>
                    </div>
                    <h3 className="font-medium text-sm truncate">{incident.title}</h3>
                    <p className="text-xs text-muted-foreground truncate mt-0.5">
                      {incident.description}
                    </p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(incident.created_at).toLocaleTimeString()}
                      </span>
                      {incident.operator_id && (
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {incident.operator_id}
                        </span>
                      )}
                      {incident.contradiction_ids?.length > 0 && (
                        <Badge variant="outline" className="text-xs">
                          {incident.contradiction_ids.length} contradictions
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
