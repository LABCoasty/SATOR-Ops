"use client"

import { useState } from "react"
import { ChevronLeft, ChevronRight, Play, Pause, FileText, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { useTimeline } from "@/hooks/use-decisions"

export function TimelineScrubber() {
  const { events, loading, error } = useTimeline()
  const [selectedIndex, setSelectedIndex] = useState(5)
  const [isPlaying, setIsPlaying] = useState(false)

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading timeline...</span>
      </div>
    )
  }

  if (error || events.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-4">
        <p className="text-center text-muted-foreground">No timeline events available</p>
      </div>
    )
  }

  const selectedEvent = events[Math.min(selectedIndex, events.length - 1)]

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold">Event Timeline</h3>
          <span className="text-xs text-muted-foreground">Scrub to inspect evidence at any moment</span>
        </div>
        <div className="flex items-center gap-2">
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
            onClick={() => setSelectedIndex(Math.min(events.length - 1, selectedIndex + 1))}
            disabled={selectedIndex === events.length - 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Timeline Track */}
      <div className="relative">
        {/* Background track */}
        <div className="h-2 rounded-full bg-muted" />

        {/* Event markers */}
        <div className="absolute inset-0 flex items-center justify-between px-1">
          {events.map((event, index) => (
            <button
              key={event.time}
              onClick={() => setSelectedIndex(index)}
              className={cn(
                "relative h-4 w-4 rounded-full border-2 transition-all",
                index === selectedIndex
                  ? "border-primary bg-primary scale-125"
                  : event.has_contradiction
                    ? "border-warning bg-warning/50 hover:scale-110"
                    : "border-muted-foreground bg-muted hover:scale-110 hover:border-foreground",
              )}
            >
              {event.has_contradiction && index !== selectedIndex && (
                <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-warning" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Event Details */}
      <div className="flex items-center justify-between rounded-md bg-muted/50 p-3">
        <div className="flex items-center gap-4">
          <div>
            <span className="font-mono text-lg font-bold">{selectedEvent.time}</span>
            <p className="text-sm text-muted-foreground">{selectedEvent.label}</p>
          </div>
          {selectedEvent.has_contradiction && (
            <span className="rounded-md bg-warning/20 px-2 py-1 text-xs font-medium text-warning">
              Contradiction detected
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
    </div>
  )
}
