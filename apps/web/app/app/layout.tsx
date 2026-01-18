import type React from "react"
import { AppShell } from "@/components/app/app-shell"
import { SimulationProvider } from "@/contexts/simulation-context"
import { VoiceCallProvider } from "@/contexts/voice-call-context"

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SimulationProvider>
      <VoiceCallProvider>
        <AppShell>{children}</AppShell>
      </VoiceCallProvider>
    </SimulationProvider>
  )
}
