"use client"

import { useState } from "react"
import { ChevronLeft, ChevronRight, Play, Pause, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import Link from "next/link"

interface TimelineEvent {
  time: string
  timestamp: number
  label: string
  trustScore: number
  hasContradiction: boolean
}

const events: TimelineEvent[] = [
  { time: "14:28:00", timestamp: 0, label: "Baseline", trustScore: 0.94, hasContradiction: false },
  { time: "14:30:15", timestamp: 1, label: "Anomaly detected", trustScore: 0.88, hasContradiction: false },
  { time: "14:32:42", timestamp: 2, label: "Sensor conflict", trustScore: 0.71, hasContradiction: true },
  { time: "14:35:08", timestamp: 3, label: "Manual override", trustScore: 0.76, hasContradiction: false },
  { time: "14:38:30", timestamp: 4, label: "Stabilized", trustScore: 0.87, hasContradiction: false },
  { time: "14:41:00", timestamp: 5, label: "Current", trustScore: 0.87, hasContradiction: false },
]

export function TimelineScrubber() {
  const [selectedIndex, setSelectedIndex] = useState(5)
  const [isPlaying, setIsPlaying] = useState(false)

  const selectedEvent = events[selectedIndex]

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
                  : event.hasContradiction
                    ? "border-warning bg-warning/50 hover:scale-110"
                    : "border-muted-foreground bg-muted hover:scale-110 hover:border-foreground",
              )}
            >
              {event.hasContradiction && index !== selectedIndex && (
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
          {selectedEvent.hasContradiction && (
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
                selectedEvent.trustScore >= 0.85
                  ? "text-success"
                  : selectedEvent.trustScore >= 0.7
                    ? "text-warning"
                    : "text-destructive",
              )}
            >
              {selectedEvent.trustScore.toFixed(2)}
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
    </div>
  )
}
