"use client"

import { FileText } from "lucide-react"

const evidence = [
  { label: "Active data sources", value: "12" },
  { label: "Total signals processed", value: "47" },
  { label: "Corroborating readings", value: "41" },
  { label: "Contradictions resolved", value: "2" },
  { label: "Data freshness", value: "< 5 seconds" },
]

export function EvidenceList() {
  return (
    <div className="border-b border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <h3 className="font-semibold">Evidence Summary</h3>
      </div>
      <div className="space-y-2">
        {evidence.map((item) => (
          <div key={item.label} className="flex items-center justify-between py-1">
            <span className="text-sm text-muted-foreground">{item.label}</span>
            <span className="font-mono text-sm font-medium">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
