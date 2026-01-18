"use client"

import { useState, useEffect, useCallback, useRef } from "react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws"

export interface TelemetryChannel {
  id: string
  name: string
  source: string
  value: number
  unit: string
  trend: "up" | "down" | "stable"
  status: "normal" | "warning" | "critical"
  sparkline: number[]
  summary: string
  min_threshold: number
  max_threshold: number
  timestamp: string
}

export interface DataSource {
  id: string
  name: string
  reliability: number
  last_update: string
  status: "online" | "degraded" | "offline"
  type: string
}

export interface SignalSummary {
  active_signals: number
  sources_reporting: number
  healthy: number
  warnings: number
  critical: number
  unknown: number
  last_sync: string
  connected: boolean
}

export function useTelemetry() {
  const [channels, setChannels] = useState<TelemetryChannel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchChannels = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/telemetry/channels`)
      if (!response.ok) throw new Error("Failed to fetch telemetry")
      const data = await response.json()
      setChannels(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchChannels()
    // Refresh every 5 seconds
    const interval = setInterval(fetchChannels, 5000)
    return () => clearInterval(interval)
  }, [fetchChannels])

  return { channels, loading, error, refetch: fetchChannels }
}

export function useDataSources() {
  const [sources, setSources] = useState<DataSource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSources() {
      try {
        const response = await fetch(`${API_URL}/telemetry/sources`)
        if (!response.ok) throw new Error("Failed to fetch sources")
        const data = await response.json()
        setSources(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error")
      } finally {
        setLoading(false)
      }
    }

    fetchSources()
  }, [])

  return { sources, loading, error }
}

export function useSignalSummary() {
  const [summary, setSummary] = useState<SignalSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSummary = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/telemetry/summary`)
      if (!response.ok) throw new Error("Failed to fetch summary")
      const data = await response.json()
      setSummary(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSummary()
    const interval = setInterval(fetchSummary, 5000)
    return () => clearInterval(interval)
  }, [fetchSummary])

  return { summary, loading, error, refetch: fetchSummary }
}

export function useTelemetryWebSocket() {
  const [channels, setChannels] = useState<TelemetryChannel[]>([])
  const [summary, setSummary] = useState<SignalSummary | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/telemetry`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log("WebSocket connected")
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === "telemetry_update") {
          setChannels(data.channels)
          setSummary(data.summary)
        }
      } catch (err) {
        console.error("WebSocket message error:", err)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      console.log("WebSocket disconnected")
    }

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
      setConnected(false)
    }

    return () => {
      ws.close()
    }
  }, [])

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "ping" }))
    }
  }, [])

  return { channels, summary, connected, sendPing }
}
