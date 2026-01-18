"use client"

import { useState, useEffect, useRef } from "react"
import { Video, ChevronLeft, ChevronRight, AlertTriangle, Shield } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SimulationEvent, ScenarioType } from "@/contexts/simulation-context"

// Video sources for different scenarios
const SCENARIO_CONFIG = {
  scenario2: {
    videoUrl: "/oil_rig.mp4",
    title: "Oil Rig Monitoring",
    badge: "SCENARIO 2",
    badgeColor: "destructive" as const,
  },
  scenario3: {
    videoUrl: "/water_pipe.mp4",
    title: "Water Pipe Monitoring",
    badge: "SCENARIO 3",
    badgeColor: "default" as const,
  },
}

interface Scenario2VideoPanelProps {
  events: SimulationEvent[]
  currentTimeSec: number
  scenario?: ScenarioType
}

export function Scenario2VideoPanel({ events, currentTimeSec, scenario = "scenario2" }: Scenario2VideoPanelProps) {
  const config = SCENARIO_CONFIG[scenario as keyof typeof SCENARIO_CONFIG] || SCENARIO_CONFIG.scenario2
  const [currentIssueIndex, setCurrentIssueIndex] = useState(0)
  const carouselRef = useRef<HTMLDivElement>(null)

  // Filter events that are actual issues (warnings/critical)
  const detectedIssues = events.filter(e => e.severity === "warning" || e.severity === "critical")

  // Auto-advance carousel when new issues arrive
  useEffect(() => {
    if (detectedIssues.length > 0) {
      setCurrentIssueIndex(detectedIssues.length - 1)
    }
  }, [detectedIssues.length])

  const goToPrevious = () => {
    setCurrentIssueIndex(prev => Math.max(0, prev - 1))
  }

  const goToNext = () => {
    setCurrentIssueIndex(prev => Math.min(detectedIssues.length - 1, prev + 1))
  }

  const currentIssue = detectedIssues[currentIssueIndex]

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden animate-in fade-in slide-in-from-left-4 duration-500">
      {/* Header */}
      <div className="border-b border-border px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Video className="h-4 w-4 text-primary" />
          <h2 className="font-semibold">{config.title}</h2>
          <Badge 
            variant={config.badgeColor === "destructive" ? "destructive" : "default"} 
            className={cn(
              "text-xs animate-pulse",
              config.badgeColor !== "destructive" && "bg-blue-500 text-white"
            )}
          >
            {config.badge}
          </Badge>
        </div>
        <span className="text-xs text-muted-foreground font-mono">
          {currentTimeSec.toFixed(0)}s
        </span>
      </div>

      {/* Video */}
      <div className="aspect-video bg-black">
        <video
          src={config.videoUrl}
          className="w-full h-full object-cover"
          autoPlay
          loop
          muted
          playsInline
        />
      </div>

      {/* Issues Carousel */}
      <div className="border-t border-border">
        <div className="px-4 py-2 flex items-center justify-between border-b border-border bg-muted/30">
          <div className="flex items-center gap-2">
            <Shield className="h-3.5 w-3.5 text-warning" />
            <span className="text-xs font-medium">Detected Issues</span>
            <Badge variant={detectedIssues.length > 0 ? "destructive" : "secondary"} className="text-xs">
              {detectedIssues.length}
            </Badge>
          </div>
          {detectedIssues.length > 1 && (
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={goToPrevious}
                disabled={currentIssueIndex === 0}
              >
                <ChevronLeft className="h-3 w-3" />
              </Button>
              <span className="text-xs text-muted-foreground font-mono min-w-[40px] text-center">
                {currentIssueIndex + 1}/{detectedIssues.length}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={goToNext}
                disabled={currentIssueIndex === detectedIssues.length - 1}
              >
                <ChevronRight className="h-3 w-3" />
              </Button>
            </div>
          )}
        </div>

        {/* Carousel Content */}
        <div ref={carouselRef} className="p-3 min-h-[80px]">
          {detectedIssues.length === 0 ? (
            <div className="flex items-center justify-center text-muted-foreground text-sm h-[60px]">
              <span>No issues detected yet...</span>
            </div>
          ) : currentIssue ? (
            <div
              className={cn(
                "p-3 rounded-lg border animate-in fade-in duration-200",
                currentIssue.severity === "critical"
                  ? "bg-destructive/10 border-destructive"
                  : "bg-warning/10 border-warning"
              )}
            >
              <div className="flex items-start gap-3">
                <AlertTriangle
                  className={cn(
                    "h-4 w-4 mt-0.5 flex-shrink-0",
                    currentIssue.severity === "critical" ? "text-destructive" : "text-warning"
                  )}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge
                      variant={currentIssue.severity === "critical" ? "destructive" : "secondary"}
                      className="text-xs"
                    >
                      {currentIssue.severity.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      @ {currentIssue.time_sec.toFixed(0)}s
                    </span>
                  </div>
                  <h4 className="font-medium text-sm">{currentIssue.title}</h4>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {currentIssue.description}
                  </p>
                </div>
              </div>
            </div>
          ) : null}
        </div>

        {/* Issue dots indicator */}
        {detectedIssues.length > 1 && (
          <div className="flex justify-center gap-1 pb-3">
            {detectedIssues.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIssueIndex(idx)}
                className={cn(
                  "h-1.5 rounded-full transition-all",
                  idx === currentIssueIndex
                    ? "w-4 bg-primary"
                    : "w-1.5 bg-muted-foreground/30 hover:bg-muted-foreground/50"
                )}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
