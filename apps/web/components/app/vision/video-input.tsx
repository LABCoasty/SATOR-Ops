"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { Video, Camera, Upload, Play, Square, Settings, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { getOvershootClient, type OvershootFrame } from "@/lib/overshoot-client"

interface VideoInputProps {
  onFrame?: (frame: OvershootFrame) => void
  className?: string
}

type VideoSource = "webcam" | "file" | "url" | "demo"

export function VideoInput({ onFrame, className }: VideoInputProps) {
  const [source, setSource] = useState<VideoSource>("demo")
  const [isProcessing, setIsProcessing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [fps, setFps] = useState(1)
  const [frameCount, setFrameCount] = useState(0)
  const [lastFrame, setLastFrame] = useState<OvershootFrame | null>(null)
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const clientRef = useRef(getOvershootClient())

  // Demo video URL (industrial footage for testing)
  const demoVideoUrl = "/demo-industrial.mp4" // Add your demo video or use placeholder

  const handleFrameReceived = useCallback((frame: OvershootFrame) => {
    setFrameCount(prev => prev + 1)
    setLastFrame(frame)
    onFrame?.(frame)
  }, [onFrame])

  const startWebcam = async () => {
    if (!videoRef.current) return
    
    setIsLoading(true)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 }
      })
      videoRef.current.srcObject = stream
      await videoRef.current.play()
      setSource("webcam")
    } catch (error) {
      console.error("Webcam error:", error)
      alert("Could not access webcam. Please check permissions.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !videoRef.current) return
    
    setIsLoading(true)
    try {
      const url = URL.createObjectURL(file)
      videoRef.current.src = url
      videoRef.current.srcObject = null
      await videoRef.current.play()
      setSource("file")
    } catch (error) {
      console.error("File load error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadDemoVideo = async () => {
    if (!videoRef.current) return
    
    setIsLoading(true)
    try {
      // Use a placeholder video that loops
      videoRef.current.src = demoVideoUrl
      videoRef.current.srcObject = null
      videoRef.current.loop = true
      await videoRef.current.play()
      setSource("demo")
    } catch (error) {
      console.error("Demo video error:", error)
      // If no demo video, use webcam or show placeholder
    } finally {
      setIsLoading(false)
    }
  }

  const startProcessing = async () => {
    if (!videoRef.current) return
    
    const client = clientRef.current
    await client.initialize(videoRef.current)
    client.startProcessing(fps, handleFrameReceived)
    setIsProcessing(true)
    setFrameCount(0)
  }

  const stopProcessing = () => {
    clientRef.current.stopProcessing()
    setIsProcessing(false)
  }

  const stopVideo = () => {
    if (!videoRef.current) return
    
    // Stop processing
    if (isProcessing) {
      stopProcessing()
    }
    
    // Stop video stream
    if (videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream
      stream.getTracks().forEach(track => track.stop())
      videoRef.current.srcObject = null
    }
    
    videoRef.current.pause()
    videoRef.current.src = ""
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopVideo()
    }
  }, [])

  return (
    <div className={cn("rounded-lg border border-border bg-card", className)}>
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Video className="h-5 w-5 text-primary" />
            <h2 className="font-semibold">Video Input</h2>
          </div>
          <div className="flex items-center gap-2">
            {isProcessing && (
              <Badge variant="default" className="gap-1 bg-green-500/20 text-green-500">
                <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                Processing
              </Badge>
            )}
            <Badge variant="outline" className="text-xs">
              {fps} FPS
            </Badge>
          </div>
        </div>
      </div>

      {/* Video Display */}
      <div className="relative aspect-video bg-black">
        <video
          ref={videoRef}
          className="w-full h-full object-contain"
          playsInline
          muted
        />
        
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <Loader2 className="h-8 w-8 animate-spin text-white" />
          </div>
        )}

        {!videoRef.current?.src && !videoRef.current?.srcObject && !isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
            <Video className="h-12 w-12 mb-2 opacity-30" />
            <p className="text-sm">Select a video source</p>
          </div>
        )}

        {/* Frame overlay */}
        {lastFrame && isProcessing && (
          <div className="absolute bottom-2 left-2 right-2 bg-black/70 rounded px-2 py-1 text-xs text-white font-mono">
            <div className="flex justify-between">
              <span>Frame: {lastFrame.frame_id}</span>
              <span>Equipment: {lastFrame.equipment_states.length}</span>
              <span>Events: {lastFrame.safety_events.length}</span>
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="p-4 space-y-4">
        {/* Source Selection */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={startWebcam}
            disabled={isProcessing}
            className="gap-1"
          >
            <Camera className="h-4 w-4" />
            Webcam
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={isProcessing}
            className="gap-1"
          >
            <Upload className="h-4 w-4" />
            Upload
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={loadDemoVideo}
            disabled={isProcessing}
            className="gap-1"
          >
            <Video className="h-4 w-4" />
            Demo
          </Button>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* Processing Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">FPS:</label>
            <select
              value={fps}
              onChange={(e) => setFps(Number(e.target.value))}
              disabled={isProcessing}
              className="text-sm border rounded px-2 py-1 bg-background"
            >
              <option value={0.5}>0.5</option>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={5}>5</option>
            </select>
          </div>

          <div className="flex gap-2">
            {!isProcessing ? (
              <Button
                onClick={startProcessing}
                disabled={!videoRef.current?.src && !videoRef.current?.srcObject}
                className="gap-1"
              >
                <Play className="h-4 w-4" />
                Start Analysis
              </Button>
            ) : (
              <Button
                variant="destructive"
                onClick={stopProcessing}
                className="gap-1"
              >
                <Square className="h-4 w-4" />
                Stop
              </Button>
            )}
          </div>
        </div>

        {/* Stats */}
        {isProcessing && (
          <div className="grid grid-cols-3 gap-4 pt-2 border-t">
            <div className="text-center">
              <div className="text-2xl font-mono font-bold">{frameCount}</div>
              <div className="text-xs text-muted-foreground">Frames Analyzed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-mono font-bold">
                {lastFrame?.equipment_states.length ?? 0}
              </div>
              <div className="text-xs text-muted-foreground">Equipment Detected</div>
            </div>
            <div className="text-center">
              <div className={cn(
                "text-2xl font-mono font-bold",
                (lastFrame?.safety_events.length ?? 0) > 0 && "text-destructive"
              )}>
                {lastFrame?.safety_events.length ?? 0}
              </div>
              <div className="text-xs text-muted-foreground">Safety Events</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
