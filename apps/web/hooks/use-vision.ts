"use client"

import { useState, useEffect, useCallback, useRef } from "react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ============================================================================
// Types
// ============================================================================

export interface VisionFrame {
  frame_id: string
  timestamp: string
  video_timestamp_ms?: number
  equipment_states: EquipmentState[]
  operator_actions: OperatorAction[]
  safety_events: SafetyEvent[]
  frame_quality: number
  scene_description?: string
}

export interface EquipmentState {
  equipment_id: string
  equipment_type: string
  name?: string
  status: "normal" | "warning" | "critical" | "unknown" | "offline"
  valve_position?: string
  gauge_reading?: {
    value: number
    unit: string
    in_normal_range: boolean
  }
  indicator_color?: string
  visual_description?: string
  confidence: number
  mapped_tag_id?: string
}

export interface OperatorAction {
  action_id: string
  person: {
    person_id: string
    wearing_ppe: boolean
    ppe_items: string[]
  }
  action_type: string
  interacting_with?: string
  interaction_description?: string
  moving_direction?: string
  speed?: string
  visual_description?: string
  confidence: number
}

export interface SafetyEvent {
  event_id: string
  event_type: string
  severity: "info" | "warning" | "critical" | "emergency"
  description: string
  visual_evidence?: string
  related_equipment: string[]
  related_persons: string[]
  confidence: number
  acknowledged: boolean
  resolved: boolean
}

export interface VisionQueueStatus {
  is_running: boolean
  queue_size: number
  processed_count: number
  delay_ms: number
  batch_size: number
  timeline_sync_enabled: boolean
  timeline_offset_sec: number
}

export interface VisionWebhookResponse {
  success: boolean
  frame_id?: string
  processed: boolean
  queued: boolean
  processing_delay_ms: number
  timeline_time_sec: number
  incident_created?: string
  message: string
}

// ============================================================================
// Hooks
// ============================================================================

export function useVisionLatest() {
  const [frame, setFrame] = useState<VisionFrame | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchLatest = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/vision/latest`)
      if (!response.ok) throw new Error("Failed to fetch latest vision")
      const data = await response.json()
      setFrame(data.frame)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLatest()
    // Refresh every 2 seconds for live updates
    const interval = setInterval(fetchLatest, 2000)
    return () => clearInterval(interval)
  }, [fetchLatest])

  return { frame, loading, error, refetch: fetchLatest }
}

export function useVisionHistory(limit: number = 10) {
  const [frames, setFrames] = useState<VisionFrame[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/vision/history?limit=${limit}`)
      if (!response.ok) throw new Error("Failed to fetch vision history")
      const data = await response.json()
      setFrames(data.frames)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  return { frames, loading, error, refetch: fetchHistory }
}

export function useVisionQueue() {
  const [status, setStatus] = useState<VisionQueueStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/vision/queue/status`)
      if (!response.ok) throw new Error("Failed to fetch queue status")
      const data = await response.json()
      setStatus(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [])

  const startQueue = useCallback(async (timelineOffsetSec: number = 0) => {
    try {
      const response = await fetch(
        `${API_URL}/api/vision/queue/start?timeline_offset_sec=${timelineOffsetSec}`,
        { method: "POST" }
      )
      if (!response.ok) throw new Error("Failed to start queue")
      await fetchStatus()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return false
    }
  }, [fetchStatus])

  const stopQueue = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/vision/queue/stop`, {
        method: "POST"
      })
      if (!response.ok) throw new Error("Failed to stop queue")
      await fetchStatus()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return false
    }
  }, [fetchStatus])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 3000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  return { status, loading, error, startQueue, stopQueue, refetch: fetchStatus }
}

export function useVisionSimulate() {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResponse, setLastResponse] = useState<VisionWebhookResponse | null>(null)

  const simulateFrame = useCallback(async (frameData: Partial<VisionFrame>) => {
    setSubmitting(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/vision/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(frameData)
      })
      if (!response.ok) throw new Error("Failed to simulate vision frame")
      const data = await response.json()
      setLastResponse(data)
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error"
      setError(errorMessage)
      throw err
    } finally {
      setSubmitting(false)
    }
  }, [])

  const sendWebhook = useCallback(async (payload: Record<string, any>) => {
    setSubmitting(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/vision/webhook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      if (!response.ok) throw new Error("Failed to send vision webhook")
      const data = await response.json()
      setLastResponse(data)
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error"
      setError(errorMessage)
      throw err
    } finally {
      setSubmitting(false)
    }
  }, [])

  return { simulateFrame, sendWebhook, submitting, error, lastResponse }
}

// Real-time vision via WebSocket
export function useVisionWebSocket() {
  const [frame, setFrame] = useState<VisionFrame | null>(null)
  const [connected, setConnected] = useState(false)
  const [safetyEvents, setSafetyEvents] = useState<SafetyEvent[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws"
    const ws = new WebSocket(`${WS_URL}/vision`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log("Vision WebSocket connected")
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === "vision_frame") {
          setFrame(data.frame)
          if (data.frame.safety_events?.length > 0) {
            setSafetyEvents(prev => [
              ...data.frame.safety_events,
              ...prev.slice(0, 19) // Keep last 20
            ])
          }
        }
      } catch (err) {
        console.error("Vision WebSocket message error:", err)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      console.log("Vision WebSocket disconnected")
    }

    ws.onerror = (error) => {
      console.error("Vision WebSocket error:", error)
      setConnected(false)
    }

    return () => {
      ws.close()
    }
  }, [])

  return { frame, connected, safetyEvents }
}
