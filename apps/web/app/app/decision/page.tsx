import { DecisionContext } from "@/components/app/decision/decision-context"
import { TimelineScrubber } from "@/components/app/decision/timeline-scrubber"
import { ContradictionsPanel } from "@/components/app/decision/contradictions-panel"
import { TrustBreakdown } from "@/components/app/decision/trust-breakdown"

export default function DecisionPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Decision / Trust</h1>
          <p className="text-sm text-muted-foreground">Analyze evidence and compute trust scores</p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-primary/50 bg-primary/10 px-3 py-1.5">
          <span className="h-2 w-2 rounded-full bg-primary" />
          <span className="text-sm font-mono text-primary">DECISION_READY</span>
        </div>
      </div>

      {/* Timeline Scrubber */}
      <TimelineScrubber />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Decision Context - Main Center Area */}
        <div className="lg:col-span-2 space-y-6">
          <DecisionContext />
          <ContradictionsPanel />
        </div>

        {/* Trust Breakdown - Right Panel */}
        <div>
          <TrustBreakdown />
        </div>
      </div>
    </div>
  )
}
