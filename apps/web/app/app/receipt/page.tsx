import { ReceiptHeader } from "@/components/app/receipt/receipt-header"
import { DecisionOutcome } from "@/components/app/receipt/decision-outcome"
import { EvidenceList } from "@/components/app/receipt/evidence-list"
import { TrustScoreCard } from "@/components/app/receipt/trust-score-card"
import { KnownUnknowns } from "@/components/app/receipt/known-unknowns"
import { ReceiptActions } from "@/components/app/receipt/receipt-actions"

export default function TrustReceiptPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Receipt Header */}
      <ReceiptHeader />

      {/* Main Receipt Content */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <DecisionOutcome />
        <EvidenceList />
        <TrustScoreCard />
        <KnownUnknowns />
      </div>

      {/* Actions */}
      <ReceiptActions />
    </div>
  )
}
