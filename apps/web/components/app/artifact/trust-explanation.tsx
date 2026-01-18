"use client"

import { Shield, AlertCircle, HelpCircle, FileText } from "lucide-react"

export function TrustExplanation() {
  const trustScore = 0.87

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-semibold">Trust Explanation</h2>
      </div>

      {/* Score Display */}
      <div className="p-4 border-b border-border">
        <div className="text-center">
          <div className="inline-flex items-center justify-center h-20 w-20 rounded-full border-4 border-success bg-success/10">
            <span className="text-2xl font-bold font-mono text-success">{trustScore.toFixed(2)}</span>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">High Confidence Decision</p>
        </div>
      </div>

      {/* Why This Score */}
      <div className="p-4 space-y-4">
        <div>
          <h4 className="text-sm font-medium flex items-center gap-2 mb-2">
            <Shield className="h-4 w-4 mode-trust-text" />
            Why This Score
          </h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Multiple independent sources corroborated the system state. Detected contradiction was minor and resolved
            algorithmically. Overall evidence chain is strong.
          </p>
        </div>

        <div>
          <h4 className="text-sm font-medium flex items-center gap-2 mb-2">
            <AlertCircle className="h-4 w-4 text-warning" />
            Limiting Factors
          </h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Flow sensor divergence reduced score by 0.08</li>
            <li>• Offline remote station added uncertainty</li>
          </ul>
        </div>

        <div>
          <h4 className="text-sm font-medium flex items-center gap-2 mb-2">
            <HelpCircle className="h-4 w-4 text-muted-foreground" />
            What Would Improve It
          </h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Restore Remote Station C connection</li>
            <li>• Calibrate Flow Sensor B</li>
            <li>• Add redundant external feed</li>
          </ul>
        </div>

        {/* Reason Codes */}
        <div className="rounded-md bg-muted/30 p-3">
          <h4 className="text-xs font-medium flex items-center gap-2 mb-2">
            <FileText className="h-3 w-3" />
            Machine-Readable Codes
          </h4>
          <div className="flex flex-wrap gap-2">
            <code className="rounded bg-card px-2 py-0.5 text-xs font-mono text-primary">TR_0x12A</code>
            <code className="rounded bg-card px-2 py-0.5 text-xs font-mono text-warning">TR_0x08B</code>
            <code className="rounded bg-card px-2 py-0.5 text-xs font-mono text-muted-foreground">TR_0x04C</code>
          </div>
        </div>
      </div>
    </div>
  )
}
