"use client"

import { useState, useEffect, useCallback } from "react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ============================================================================
// Types
// ============================================================================

export interface Incident {
  incident_id: string
  scenario_id: string
  title: string
  description: string
  severity: "info" | "warning" | "critical" | "emergency"
  state: "open" | "acknowledged" | "resolved" | "closed"
  contradiction_ids: string[]
  decision_card_id?: string
  operator_id?: string
  created_at: string
  acknowledged_at?: string
  resolved_at?: string
  resolution_summary?: string
}

export interface DecisionCard {
  card_id: string
  incident_id: string
  title: string
  summary: string
  severity: string
  trust_score: number
  reason_codes: string[]
  predictions: Prediction[]
  contradictions: Contradiction[]
  allowed_actions: AllowedAction[]
  recommended_action_id: string
  recommendation_rationale: string
  questions: OperatorQuestion[]
  expires_at?: string
  created_at: string
}

export interface Prediction {
  prediction_id: string
  issue_type: string
  description: string
  confidence: number
  time_horizon: string
  explanation: string
  recommended_action: string
}

export interface Contradiction {
  contradiction_id: string
  reason_code: string
  category: string
  description: string
  values: Record<string, any>
  confidence: number
  severity: string
}

export interface AllowedAction {
  action_id: string
  action_type: "act" | "defer" | "escalate"
  label: string
  description: string
  risk_level: string
}

export interface OperatorQuestion {
  question_id: string
  question_type: string
  question_text: string
  options?: { option_id: string; label: string; description?: string }[]
  answered: boolean
  answer?: any
}

// ============================================================================
// Hooks
// ============================================================================

export function useIncidents(scenarioId?: string) {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIncidents = useCallback(async () => {
    try {
      const url = scenarioId 
        ? `${API_URL}/api/incidents?scenario_id=${scenarioId}`
        : `${API_URL}/api/incidents`
      const response = await fetch(url)
      if (!response.ok) throw new Error("Failed to fetch incidents")
      const data = await response.json()
      setIncidents(data.incidents || data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [scenarioId])

  useEffect(() => {
    fetchIncidents()
    // Poll for updates every 3 seconds
    const interval = setInterval(fetchIncidents, 3000)
    return () => clearInterval(interval)
  }, [fetchIncidents])

  return { incidents, loading, error, refetch: fetchIncidents }
}

export function useIncident(incidentId: string) {
  const [incident, setIncident] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIncident = useCallback(async () => {
    if (!incidentId) return
    try {
      const response = await fetch(`${API_URL}/api/incidents/${incidentId}`)
      if (!response.ok) throw new Error("Failed to fetch incident")
      const data = await response.json()
      setIncident(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [incidentId])

  const acknowledgeIncident = useCallback(async (operatorId: string) => {
    try {
      const response = await fetch(
        `${API_URL}/api/incidents/${incidentId}/acknowledge`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ operator_id: operatorId })
        }
      )
      if (!response.ok) throw new Error("Failed to acknowledge incident")
      await fetchIncident()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return false
    }
  }, [incidentId, fetchIncident])

  const resolveIncident = useCallback(async (
    operatorId: string,
    resolutionSummary: string,
    actionTaken: string
  ) => {
    try {
      const response = await fetch(
        `${API_URL}/api/incidents/${incidentId}/resolve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            operator_id: operatorId,
            resolution_summary: resolutionSummary,
            action_taken: actionTaken
          })
        }
      )
      if (!response.ok) throw new Error("Failed to resolve incident")
      await fetchIncident()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return false
    }
  }, [incidentId, fetchIncident])

  useEffect(() => {
    fetchIncident()
  }, [fetchIncident])

  return {
    incident,
    loading,
    error,
    refetch: fetchIncident,
    acknowledgeIncident,
    resolveIncident
  }
}

export function useDecisionCard(incidentId: string) {
  const [card, setCard] = useState<DecisionCard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCard = useCallback(async () => {
    if (!incidentId) return
    try {
      const response = await fetch(
        `${API_URL}/api/incidents/${incidentId}/decision-card`
      )
      if (response.status === 404) {
        setCard(null)
        setError(null)
        return
      }
      if (!response.ok) throw new Error("Failed to fetch decision card")
      const data = await response.json()
      setCard(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [incidentId])

  const submitAction = useCallback(async (actionId: string, rationale?: string) => {
    try {
      const response = await fetch(
        `${API_URL}/api/incidents/${incidentId}/action`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action_id: actionId,
            rationale: rationale || ""
          })
        }
      )
      if (!response.ok) throw new Error("Failed to submit action")
      await fetchCard()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return false
    }
  }, [incidentId, fetchCard])

  const answerQuestion = useCallback(async (questionId: string, answer: any) => {
    try {
      const response = await fetch(
        `${API_URL}/api/incidents/${incidentId}/questions/${questionId}/answer`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answer })
        }
      )
      if (!response.ok) throw new Error("Failed to submit answer")
      await fetchCard()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return false
    }
  }, [incidentId, fetchCard])

  useEffect(() => {
    fetchCard()
  }, [fetchCard])

  return { card, loading, error, refetch: fetchCard, submitAction, answerQuestion }
}

export function useActiveIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchActive = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/incidents?state=open`)
      if (!response.ok) throw new Error("Failed to fetch active incidents")
      const data = await response.json()
      setIncidents(data.incidents || data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchActive()
    const interval = setInterval(fetchActive, 2000)
    return () => clearInterval(interval)
  }, [fetchActive])

  return { incidents, loading, error, refetch: fetchActive }
}
