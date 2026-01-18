import { DecisionContext } from "@/components/app/decision/decision-context"
import { TimelineScrubber } from "@/components/app/decision/timeline-scrubber"
import { ContradictionsPanel } from "@/components/app/decision/contradictions-panel"
import { TrustBreakdown } from "@/components/app/decision/trust-breakdown"
import { EventLog } from "@/components/app/decision/event-log"
import { OperatorDecisionsLog } from "@/components/app/decision/operator-decisions-log"

export default function DecisionPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Decision / Trust</h1>
          <p className="text-sm text-muted-foreground">Analyze evidence and compute trust scores</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-md border border-green-500/50 bg-green-500/10 px-3 py-1.5">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm font-mono text-green-500">DECISION_READY</span>
          </div>
        </div>
      </div>

      {/* Timeline Scrubber */}
      <TimelineScrubber />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Event Log & Operator Decisions */}
        <div className="space-y-6">
          <EventLog />
          <OperatorDecisionsLog />
        </div>

        {/* Center Column - Decision Context & Contradictions */}
        <div className="space-y-6">
          <DecisionContext />
          <ContradictionsPanel />
        </div>

        {/* Right Column - Trust Breakdown */}
        <div>
          <TrustBreakdown />
        </div>
      </div>
    </div>
  )
}
