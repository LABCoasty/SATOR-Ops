"use client"

import type React from "react"
import { useState, useCallback, useEffect, useRef } from "react"
import { AppSidebar } from "./app-sidebar"
import { AppTopBar } from "./app-top-bar"
import { AgentPanel } from "./agent-panel"
import { AgentButton } from "./agent-button"
import { VideoAlertModal, type Scenario2Result } from "./vision/video-alert-modal"

export type AppMode = "ingest" | "decision" | "artifact"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// YouTube video URL for Scenario 2
const YOUTUBE_VIDEO_ID = "IPpKZx854VQ"
const DEFAULT_VIDEO_URL = `https://www.youtube.com/watch?v=${YOUTUBE_VIDEO_ID}`
const YOUTUBE_EMBED_URL = `https://www.youtube.com/embed/${YOUTUBE_VIDEO_ID}`

export function AppShell({ children }: { children: React.ReactNode }) {
  const [agentOpen, setAgentOpen] = useState(false)

  // Scenario 2 processing state
  const [scenario2ModalOpen, setScenario2ModalOpen] = useState(false)
  const [scenario2Processing, setScenario2Processing] = useState(false)
  const [scenario2Progress, setScenario2Progress] = useState(0)
  const [scenario2Message, setScenario2Message] = useState("")
  const [scenario2Result, setScenario2Result] = useState<Scenario2Result | null>(null)
  const [videoUrl, setVideoUrl] = useState(DEFAULT_VIDEO_URL)

  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  const handleScenario2 = useCallback(async () => {
    // Reset state
    setScenario2Result(null)
    setScenario2Progress(0)
    setScenario2Message("Starting video processing...")
    setScenario2Processing(true)
    // Hide modal during processing - only show after completion
    setScenario2ModalOpen(false)

    try {
      // Start async processing
      const response = await fetch(`${API_URL}/scenario2/process-video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_url: DEFAULT_VIDEO_URL, // Use YouTube URL
          fps: 1.0,
          max_frames: 5,
          scenario_id: `ui-scenario2-${Date.now()}`
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const jobData = await response.json()
      const jobId = jobData.job_id

      // Poll for status
      pollingRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`${API_URL}/scenario2/process-video/${jobId}`)
          const status = await statusResponse.json()

          setScenario2Progress(status.progress)
          setScenario2Message(status.message)

          if (status.status === "completed" || status.status === "error") {
            if (pollingRef.current) {
              clearInterval(pollingRef.current)
              pollingRef.current = null
            }

            setScenario2Processing(false)

            if (status.result) {
              setScenario2Result(status.result)
            } else {
              setScenario2Result({
                success: status.status === "completed",
                video_url: videoUrl,
                frame_count: 0,
                incidents_created: 0,
                contradictions_found: 0,
                predictions_made: 0,
                processing_time_ms: 0,
                incidents: [],
                error: status.status === "error" ? status.message : undefined
              })
            }

            // Show modal as alert after processing completes
            if (status.status === "completed" || status.status === "error") {
              setScenario2ModalOpen(true)
            }
          }
        } catch (pollError) {
          console.error("Polling error:", pollError)
        }
      }, 500)

    } catch (error) {
      console.error("Scenario 2 error:", error)
      setScenario2Processing(false)
      setScenario2Result({
        success: false,
        video_url: videoUrl,
        frame_count: 0,
        incidents_created: 0,
        contradictions_found: 0,
        predictions_made: 0,
        processing_time_ms: 0,
        incidents: [],
        error: error instanceof Error ? error.message : "Unknown error"
      })
    }
  }, [videoUrl])

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Left Sidebar Navigation */}
      <AppSidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Status Bar */}
        <AppTopBar
          onAgentToggle={() => setAgentOpen(!agentOpen)}
          agentOpen={agentOpen}
          onScenario2={handleScenario2}
          scenario2Loading={scenario2Processing}
        />

        {/* Main Canvas with optional right panel */}
        <div className="flex flex-1 overflow-hidden relative">
          <main className="flex-1 overflow-auto p-6">{children}</main>

          {/* Agent Insight Panel */}
          {agentOpen && <AgentPanel onClose={() => setAgentOpen(false)} />}

          {!agentOpen && <AgentButton onClick={() => setAgentOpen(true)} />}
        </div>
      </div>

      {/* Scenario 2 Video Alert Modal - Only shown after processing completes */}
      <VideoAlertModal
        open={scenario2ModalOpen && !scenario2Processing}
        onOpenChange={setScenario2ModalOpen}
        processing={false}
        progress={scenario2Progress}
        progressMessage={scenario2Message}
        result={scenario2Result}
        videoUrl={YOUTUBE_EMBED_URL}
      />
    </div>
  )
}
