import type React from "react"
import { AppShell } from "@/components/app/app-shell"
import { SimulationProvider } from "@/contexts/simulation-context"

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SimulationProvider>
      <AppShell>{children}</AppShell>
    </SimulationProvider>
  )
}
