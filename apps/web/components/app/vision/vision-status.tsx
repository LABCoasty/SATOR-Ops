"use client"

import { Video, Wifi, WifiOff, Activity, AlertTriangle, Clock, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { useVisionQueue, useVisionLatest } from "@/hooks/use-vision"

export function VisionStatus() {
  const { status, loading: queueLoading, startQueue, stopQueue } = useVisionQueue()
  const { frame, loading: frameLoading } = useVisionLatest()

  const loading = queueLoading || frameLoading

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-6 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading vision status...</span>
      </div>
    )
  }

  const isConnected = status?.is_running ?? false
  const safetyEventCount = frame?.safety_events?.length ?? 0
  const equipmentCount = frame?.equipment_states?.length ?? 0

  return (
    <div className="rounded-lg border border-border bg-card">
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Video className="h-5 w-5 text-primary" />
            <h2 className="font-semibold">Vision Feed Status</h2>
          </div>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Badge variant="default" className="gap-1 bg-green-500/20 text-green-500 border-green-500/30">
                <Wifi className="h-3 w-3" />
                Connected
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1 text-muted-foreground">
                <WifiOff className="h-3 w-3" />
                Disconnected
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4">
        {/* Queue Status */}
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">Queue Size</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-mono font-bold">{status?.queue_size ?? 0}</span>
            <span className="text-xs text-muted-foreground">frames</span>
          </div>
        </div>

        {/* Processing Delay */}
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">Processing Delay</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-mono font-bold">{status?.delay_ms ?? 0}</span>
            <span className="text-xs text-muted-foreground">ms</span>
          </div>
        </div>

        {/* Processed Count */}
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">Processed</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-mono font-bold">{status?.processed_count ?? 0}</span>
            <span className="text-xs text-muted-foreground">total</span>
          </div>
        </div>

        {/* Safety Events */}
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">Safety Events</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-2xl font-mono font-bold ${safetyEventCount > 0 ? 'text-destructive' : ''}`}>
              {safetyEventCount}
            </span>
            <span className="text-xs text-muted-foreground">active</span>
          </div>
        </div>
      </div>

      {/* Latest Frame Info */}
      {frame && (
        <div className="border-t border-border px-4 py-3">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1 text-muted-foreground">
                <Activity className="h-4 w-4" />
                <span>{equipmentCount} equipment</span>
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>Frame: {frame.frame_id}</span>
              </div>
            </div>
            <span className="text-xs text-muted-foreground font-mono">
              Quality: {Math.round((frame.frame_quality ?? 1) * 100)}%
            </span>
          </div>
        </div>
      )}

      {/* Queue Controls */}
      <div className="border-t border-border px-4 py-3 flex justify-between items-center">
        <div className="text-xs text-muted-foreground">
          Timeline sync: {status?.timeline_sync_enabled ? 'Enabled' : 'Disabled'}
          {status?.timeline_offset_sec ? ` (offset: ${status.timeline_offset_sec}s)` : ''}
        </div>
        <div className="flex gap-2">
          {isConnected ? (
            <button
              onClick={() => stopQueue()}
              className="px-3 py-1 text-xs rounded-md border border-border hover:bg-muted transition-colors"
            >
              Stop Queue
            </button>
          ) : (
            <button
              onClick={() => startQueue(0)}
              className="px-3 py-1 text-xs rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Start Queue
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
