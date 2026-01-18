"use client"

import { useState, useEffect, useCallback } from "react"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const API_URL = `${API_BASE}/api`

export interface TimelineEvent {
  time: string
  timestamp: number
  label: string
  trust_score: number
  has_contradiction: boolean
  description: string
}

export interface Contradiction {
  id: string
  sources: string[]
  values: string[]
  severity: "low" | "medium" | "high"
  resolution: string
}

export interface TrustFactor {
  label: string
  value: number
  impact: "positive" | "negative" | "neutral"
}

export interface TrustBreakdown {
  composite_score: number
  factors: TrustFactor[]
  reason_codes: Array<{ code: string; description: string }>
}

export interface DecisionContext {
  current_assessment: string
  trust_score: number
  evidence_count: number
  contradictions_count: number
  known_unknowns: string[]
}

export function useTimeline() {
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchTimeline() {
      try {
        const response = await fetch(`${API_URL}/decisions/timeline`)
        if (!response.ok) throw new Error("Failed to fetch timeline")
        const data = await response.json()
        setEvents(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error")
      } finally {
        setLoading(false)
      }
    }

    fetchTimeline()
  }, [])

  return { events, loading, error }
}

export function useContradictions() {
  const [contradictions, setContradictions] = useState<Contradiction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchContradictions() {
      try {
        const response = await fetch(`${API_URL}/evidence/conflicts`)
        if (!response.ok) throw new Error("Failed to fetch contradictions")
        const data = await response.json()
        setContradictions(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error")
      } finally {
        setLoading(false)
      }
    }

    fetchContradictions()
  }, [])

  return { contradictions, loading, error }
}

export function useTrustBreakdown() {
  const [breakdown, setBreakdown] = useState<TrustBreakdown | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchBreakdown = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/decisions/trust-breakdown`)
      if (!response.ok) throw new Error("Failed to fetch trust breakdown")
      const data = await response.json()
      setBreakdown(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBreakdown()
  }, [fetchBreakdown])

  return { breakdown, loading, error, refetch: fetchBreakdown }
}

export function useDecisionContext() {
  const [context, setContext] = useState<DecisionContext | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchContext() {
      try {
        const response = await fetch(`${API_URL}/decisions/context`)
        if (!response.ok) throw new Error("Failed to fetch context")
        const data = await response.json()
        setContext(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error")
      } finally {
        setLoading(false)
      }
    }

    fetchContext()
  }, [])

  return { context, loading, error }
}

export function useEvidence() {
  const [evidence, setEvidence] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchEvidence() {
      try {
        const response = await fetch(`${API_URL}/evidence/`)
        if (!response.ok) throw new Error("Failed to fetch evidence")
        const data = await response.json()
        setEvidence(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error")
      } finally {
        setLoading(false)
      }
    }

    fetchEvidence()
  }, [])

  return { evidence, loading, error }
}
