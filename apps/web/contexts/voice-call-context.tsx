"use client"

import React, { createContext, useContext, useState, useCallback } from "react"
import VoiceCallModal from "@/components/voiceover/VoiceCallModal"
import { useOptionalSimulationContext } from "@/contexts/simulation-context"

interface VoiceCallContextData {
  currentPage?: string
  incidentId?: string
  trustScore?: number
  trustState?: string
  decisionId?: string
  decisionTitle?: string
  escalationType?: string
}

interface VoiceCallContextType {
  isCallActive: boolean
  triggerCall: (context?: VoiceCallContextData) => void
  endCall: () => void
}

const VoiceCallContext = createContext<VoiceCallContextType | null>(null)

export function useVoiceCallContext() {
  const context = useContext(VoiceCallContext)
  if (!context) {
    throw new Error("useVoiceCallContext must be used within VoiceCallProvider")
  }
  return context
}

// Optional hook that returns null if not in provider
export function useOptionalVoiceCallContext() {
  return useContext(VoiceCallContext)
}

// Inner provider that has access to simulation context
function VoiceCallProviderInner({ children }: { children: React.ReactNode }) {
  const [isCallActive, setIsCallActive] = useState(false)
  const [callContext, setCallContext] = useState<VoiceCallContextData | undefined>()
  
  // Get simulation context to pause/resume during call
  const simulationContext = useOptionalSimulationContext()

  const triggerCall = useCallback((context?: VoiceCallContextData) => {
    setCallContext(context)
    setIsCallActive(true)
    
    // Pause the simulation when escalation call starts
    if (simulationContext?.pauseSimulation) {
      simulationContext.pauseSimulation("Supervisor call in progress")
    }
  }, [simulationContext])

  const endCall = useCallback(() => {
    setIsCallActive(false)
    setCallContext(undefined)
    
    // Resume the simulation when call ends
    if (simulationContext?.resumeSimulation) {
      simulationContext.resumeSimulation()
    }
  }, [simulationContext])

  const value: VoiceCallContextType = {
    isCallActive,
    triggerCall,
    endCall,
  }

  return (
    <VoiceCallContext.Provider value={value}>
      {children}
      {isCallActive && (
        <VoiceCallModal
          context={callContext}
          onClose={endCall}
        />
      )}
    </VoiceCallContext.Provider>
  )
}

// Wrapper that ensures proper provider ordering
export function VoiceCallProvider({ children }: { children: React.ReactNode }) {
  return <VoiceCallProviderInner>{children}</VoiceCallProviderInner>
}
