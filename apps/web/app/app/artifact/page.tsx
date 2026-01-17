import { ArtifactHeader } from "@/components/app/artifact/artifact-header"
import { EventTimeline } from "@/components/app/artifact/event-timeline"
import { DecisionSummary } from "@/components/app/artifact/decision-summary"
import { TrustExplanation } from "@/components/app/artifact/trust-explanation"
import { TelemetryReferences } from "@/components/app/artifact/telemetry-references"

export default function ArtifactPage() {
  return (
    <div className="space-y-6">
      {/* Artifact Header */}
      <ArtifactHeader />

      {/* Report Layout */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <DecisionSummary />
          <EventTimeline />
          <TelemetryReferences />
        </div>

        {/* Side Panel */}
        <div>
          <TrustExplanation />
        </div>
      </div>
    </div>
  )
}
