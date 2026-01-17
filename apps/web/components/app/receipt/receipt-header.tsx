"use client"

import { Receipt, Shield } from "lucide-react"

export function ReceiptHeader() {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/20">
          <Receipt className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Trust Receipt</h1>
          <p className="text-sm text-muted-foreground">Structured audit document for decision ART-2026-0117-001</p>
        </div>
      </div>
      <div className="flex items-center gap-2 rounded-md border border-success/50 bg-success/10 px-3 py-1.5">
        <Shield className="h-4 w-4 text-success" />
        <span className="text-sm font-medium text-success">Verified</span>
      </div>
    </div>
  )
}
