"use client"

import { useState, useEffect } from "react"
import { Video, AlertTriangle, CheckCircle, Loader2, X, ExternalLink } from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

export interface Scenario2Result {
  success: boolean
  video_url: string
  frame_count: number
  incidents_created: number
  contradictions_found: number
  predictions_made: number
  processing_time_ms: number
  incidents: Array<{
    incident_id: string
    title: string
    severity: string
  }>
  error?: string
}

interface VideoAlertModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  processing: boolean
  progress: number
  progressMessage: string
  result: Scenario2Result | null
  videoUrl?: string
}

export function VideoAlertModal({
  open,
  onOpenChange,
  processing,
  progress,
  progressMessage,
  result,
  videoUrl
}: VideoAlertModalProps) {
  const [showVideo, setShowVideo] = useState(false)

  useEffect(() => {
    if (result?.success) {
      // Show video after successful processing
      setShowVideo(true)
    }
  }, [result])

  const handleViewVisionPage = () => {
    onOpenChange(false)
    window.location.href = "/app/vision"
  }

  // Don't render if processing (should be hidden)
  if (processing) {
    return null
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Video className="h-5 w-5 text-primary" />
            Scenario 2 - Video Analysis Complete
          </DialogTitle>
          <DialogDescription>
            Video has been processed and analyzed for safety events and anomalies.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Processing State - Should not show, but kept for safety */}
          {processing && (
            <div className="space-y-4">
              <div className="flex items-center justify-center py-8">
                <div className="relative">
                  <Loader2 className="h-16 w-16 animate-spin text-primary" />
                  <Video className="h-6 w-6 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-primary" />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{progressMessage}</span>
                  <span className="font-mono">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>

              <div className="bg-muted/50 rounded-lg p-4 text-sm space-y-2">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "h-2 w-2 rounded-full",
                    progress >= 20 ? "bg-green-500" : "bg-muted-foreground"
                  )} />
                  <span className={progress >= 20 ? "text-foreground" : "text-muted-foreground"}>
                    Sending video to Overshoot AI
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "h-2 w-2 rounded-full",
                    progress >= 40 ? "bg-green-500" : "bg-muted-foreground"
                  )} />
                  <span className={progress >= 40 ? "text-foreground" : "text-muted-foreground"}>
                    Extracting frames and equipment states
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "h-2 w-2 rounded-full",
                    progress >= 60 ? "bg-green-500" : "bg-muted-foreground"
                  )} />
                  <span className={progress >= 60 ? "text-foreground" : "text-muted-foreground"}>
                    Processing through LeanMCP pipeline
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "h-2 w-2 rounded-full",
                    progress >= 80 ? "bg-green-500" : "bg-muted-foreground"
                  )} />
                  <span className={progress >= 80 ? "text-foreground" : "text-muted-foreground"}>
                    Detecting contradictions and predictions
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "h-2 w-2 rounded-full",
                    progress >= 100 ? "bg-green-500" : "bg-muted-foreground"
                  )} />
                  <span className={progress >= 100 ? "text-foreground" : "text-muted-foreground"}>
                    Creating incidents and decision cards
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Result State - Always show when modal is open */}
          {result && (
            <div className="space-y-4">
              {/* Status Banner */}
              <div className={cn(
                "flex items-center gap-3 p-4 rounded-lg",
                result.success ? "bg-green-500/10" : "bg-destructive/10"
              )}>
                {result.success ? (
                  <CheckCircle className="h-6 w-6 text-green-500" />
                ) : (
                  <AlertTriangle className="h-6 w-6 text-destructive" />
                )}
                <div>
                  <h3 className="font-medium">
                    {result.success ? "Analysis Complete" : "Processing Error"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {result.success
                      ? `Processed in ${(result.processing_time_ms / 1000).toFixed(1)}s`
                      : result.error
                    }
                  </p>
                </div>
              </div>

              {/* Video Display - YouTube iframe or regular video */}
              {result.success && showVideo && (result.video_url || videoUrl) && (
                <div className="rounded-lg overflow-hidden border border-border bg-black">
                  {videoUrl && videoUrl.includes("youtube.com/embed") ? (
                    <iframe
                      src={videoUrl}
                      className="w-full aspect-video"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                      title="Processed Video"
                    />
                  ) : (
                    <video
                      src={result.video_url || videoUrl}
                      controls
                      className="w-full aspect-video"
                      autoPlay
                      muted
                    />
                  )}
                </div>
              )}

              {/* Stats Grid */}
              {result.success && (
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-mono font-bold">{result.frame_count}</div>
                    <div className="text-xs text-muted-foreground">Frames</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className={cn(
                      "text-2xl font-mono font-bold",
                      result.incidents_created > 0 && "text-destructive"
                    )}>
                      {result.incidents_created}
                    </div>
                    <div className="text-xs text-muted-foreground">Incidents</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-mono font-bold">{result.contradictions_found}</div>
                    <div className="text-xs text-muted-foreground">Contradictions</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-mono font-bold">{result.predictions_made}</div>
                    <div className="text-xs text-muted-foreground">Predictions</div>
                  </div>
                </div>
              )}

              {/* Incidents List */}
              {result.success && result.incidents.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Created Incidents</h4>
                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {result.incidents.map((incident) => (
                      <div
                        key={incident.incident_id}
                        className="flex items-center justify-between p-3 rounded-lg border bg-card"
                      >
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              incident.severity === "emergency" ? "destructive" :
                                incident.severity === "critical" ? "destructive" :
                                  "secondary"
                            }
                            className="text-xs"
                          >
                            {incident.severity}
                          </Badge>
                          <span className="text-sm">{incident.title}</span>
                        </div>
                        <span className="text-xs text-muted-foreground font-mono">
                          {incident.incident_id.slice(0, 8)}...
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {!processing && result?.success && (
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
            <Button onClick={handleViewVisionPage} className="gap-2">
              <ExternalLink className="h-4 w-4" />
              View in Vision Page
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
