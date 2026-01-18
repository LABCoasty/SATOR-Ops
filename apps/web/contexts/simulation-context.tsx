"use client"

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from "react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface SimulationState {
  simulation_id: string
  status: string
  current_time_sec: number
  total_duration_sec: number
  progress_percent: number
  trust_score: number
  phase: string
  events_triggered: number
  pending_decisions: number
  decisions_made: number
}

export interface SimulationEvent {
  event_id: string
  time_sec: number
  title: string
  description: string
  severity: "info" | "warning" | "critical"
  requires_decision: boolean
  timestamp?: string
}

export interface SimulationDecision {
  decision_id: string
  event_id: string
  time_sec: number
  title: string
  description: string
  severity: "info" | "warning" | "critical"
  decision_type: "acknowledge" | "binary" | "multi_choice" | "escalate"
  options: string[]
  prompt: string
  expires_in_sec: number | null
  responded: boolean
}

export interface SimulationTelemetry {
  time_sec: number
  channels: Record<string, { value: number; unit: string; status: string }>
  anomalies: string[]
  trust_score: number
}

interface SimulationContextType {
  // State
  simulationId: string | null
  state: SimulationState | null
  events: SimulationEvent[]
  decisions: SimulationDecision[]
  telemetry: SimulationTelemetry | null
  
  // Status
  isRunning: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  startSimulation: (scenarioType: "scenario1" | "scenario2") => Promise<void>
  stopSimulation: () => Promise<void>
  submitDecision: (decisionId: string, response: string) => Promise<boolean>
}

const SimulationContext = createContext<SimulationContextType | null>(null)

export function useSimulationContext() {
  const context = useContext(SimulationContext)
  if (!context) {
    throw new Error("useSimulationContext must be used within SimulationProvider")
  }
  return context
}

// Optional hook that returns null if not in provider (for components that may be outside)
export function useOptionalSimulationContext() {
  return useContext(SimulationContext)
}

export function SimulationProvider({ children }: { children: React.ReactNode }) {
  const [simulationId, setSimulationId] = useState<string | null>(null)
  const [state, setState] = useState<SimulationState | null>(null)
  const [events, setEvents] = useState<SimulationEvent[]>([])
  const [decisions, setDecisions] = useState<SimulationDecision[]>([])
  const [telemetry, setTelemetry] = useState<SimulationTelemetry | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const lastEventTimeSec = useRef<number>(0)

  // Polling function
  const poll = useCallback(async (simId: string) => {
    try {
      // Fetch state
      const stateRes = await fetch(`${API_URL}/simulation/enhanced/${simId}/state`)
      if (stateRes.ok) {
        const stateData = await stateRes.json()
        setState(stateData)
        
        // Check if simulation completed
        if (stateData.status === "completed" || stateData.status === "stopped") {
          if (pollingRef.current) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
        }
      }
      
      // Fetch new events (since last known time)
      const eventsRes = await fetch(
        `${API_URL}/simulation/enhanced/${simId}/events?since_sec=${lastEventTimeSec.current}`
      )
      if (eventsRes.ok) {
        const eventsData = await eventsRes.json()
        if (eventsData.events && eventsData.events.length > 0) {
          setEvents(prev => {
            const newEvents = eventsData.events.filter(
              (e: SimulationEvent) => !prev.some(pe => pe.event_id === e.event_id)
            )
            if (newEvents.length > 0) {
              lastEventTimeSec.current = Math.max(
                ...newEvents.map((e: SimulationEvent) => e.time_sec)
              )
            }
            return [...prev, ...newEvents]
          })
        }
      }
      
      // Fetch pending decisions
      const decisionsRes = await fetch(`${API_URL}/simulation/enhanced/${simId}/decisions`)
      if (decisionsRes.ok) {
        const decisionsData = await decisionsRes.json()
        setDecisions(decisionsData)
      }
      
      // Fetch telemetry
      const telemetryRes = await fetch(`${API_URL}/simulation/enhanced/${simId}/telemetry`)
      if (telemetryRes.ok) {
        const telemetryData = await telemetryRes.json()
        setTelemetry(telemetryData)
      }
      
    } catch (err) {
      console.error("Polling error:", err)
    }
  }, [])

  // Start polling when simulation ID changes
  useEffect(() => {
    if (simulationId && state?.status === "running") {
      // Poll every 500ms for fast responsive updates
      pollingRef.current = setInterval(() => poll(simulationId), 500)
      
      return () => {
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
      }
    }
  }, [simulationId, state?.status, poll])

  // Start simulation
  const startSimulation = useCallback(async (scenarioType: "scenario1" | "scenario2") => {
    setIsLoading(true)
    setError(null)
    setEvents([])
    setDecisions([])
    setTelemetry(null)
    lastEventTimeSec.current = 0
    
    try {
      const response = await fetch(`${API_URL}/simulation/enhanced/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_type: scenarioType })
      })
      
      if (!response.ok) {
        throw new Error(`Failed to start simulation: ${response.status}`)
      }
      
      const data = await response.json()
      setSimulationId(data.simulation_id)
      
      // Initial state
      setState({
        simulation_id: data.simulation_id,
        status: "running",
        current_time_sec: 0,
        total_duration_sec: 60,
        progress_percent: 0,
        trust_score: 0.95,
        phase: "monitoring",
        events_triggered: 0,
        pending_decisions: 0,
        decisions_made: 0
      })
      
      // Start immediate poll
      setTimeout(() => poll(data.simulation_id), 500)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setIsLoading(false)
    }
  }, [poll])

  // Stop simulation
  const stopSimulation = useCallback(async () => {
    if (!simulationId) return
    
    try {
      await fetch(`${API_URL}/simulation/enhanced/${simulationId}/stop`, {
        method: "POST"
      })
      
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
      
      setState(prev => prev ? { ...prev, status: "stopped" } : null)
      
    } catch (err) {
      console.error("Stop error:", err)
    }
  }, [simulationId])

  // Submit decision
  const submitDecision = useCallback(async (decisionId: string, response: string): Promise<boolean> => {
    if (!simulationId) return false
    
    try {
      const res = await fetch(
        `${API_URL}/simulation/enhanced/${simulationId}/decisions/${decisionId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ response })
        }
      )
      
      if (res.ok) {
        // Remove from pending decisions
        setDecisions(prev => prev.filter(d => d.decision_id !== decisionId))
        
        // Update state
        const data = await res.json()
        if (data.new_trust_score) {
          setState(prev => prev ? { ...prev, trust_score: data.new_trust_score, decisions_made: prev.decisions_made + 1 } : null)
        }
        
        return true
      }
      
      return false
      
    } catch (err) {
      console.error("Submit decision error:", err)
      return false
    }
  }, [simulationId])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  const value: SimulationContextType = {
    simulationId,
    state,
    events,
    decisions,
    telemetry,
    isRunning: state?.status === "running",
    isLoading,
    error,
    startSimulation,
    stopSimulation,
    submitDecision
  }

  return (
    <SimulationContext.Provider value={value}>
      {children}
    </SimulationContext.Provider>
  )
}
