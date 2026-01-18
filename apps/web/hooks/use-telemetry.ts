"use client"

import { useState, useEffect, useCallback, useRef } from "react"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"

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
      const response = await fetch(`${API_BASE}/api/telemetry/channels`)
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
        const response = await fetch(`${API_BASE}/api/telemetry/sources`)
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
      const response = await fetch(`${API_BASE}/api/telemetry/summary`)
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
    // Check if WebSocket is supported
    if (typeof WebSocket === 'undefined') {
      console.warn("WebSocket not supported in this browser")
      return
    }

    let ws: WebSocket | null = null
    let reconnectTimeout: NodeJS.Timeout | null = null
    let reconnectAttempts = 0
    const maxReconnectAttempts = 5
    const reconnectDelay = 3000

    const connect = () => {
      try {
        ws = new WebSocket(`${WS_BASE}/ws/telemetry`)
        wsRef.current = ws

        ws.onopen = () => {
          setConnected(true)
          reconnectAttempts = 0
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

        ws.onclose = (event) => {
          setConnected(false)
          console.log("WebSocket disconnected", event.code, event.reason)
          
          // Attempt to reconnect if not a normal closure
          if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++
            console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`)
            reconnectTimeout = setTimeout(connect, reconnectDelay)
          }
        }

        ws.onerror = (error) => {
          console.error("WebSocket error:", error)
          setConnected(false)
        }
      } catch (error) {
        console.error("Failed to create WebSocket:", error)
        setConnected(false)
      }
    }

    connect()

    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
      if (ws) {
        ws.close(1000, "Component unmounting")
      }
      wsRef.current = null
    }
  }, [])

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "ping" }))
    }
  }, [])

  return { channels, summary, connected, sendPing }
}
