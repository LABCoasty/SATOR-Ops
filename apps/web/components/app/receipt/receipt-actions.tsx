"use client"

import { Download, Share2, ShieldCheck, Printer } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ReceiptActions() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <ShieldCheck className="h-4 w-4" />
          <span>This receipt can be independently verified using hash 0x7a3f...b2c1</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2 bg-transparent">
            <Printer className="h-4 w-4" />
            Print
          </Button>
          <Button variant="outline" size="sm" className="gap-2 bg-transparent">
            <Share2 className="h-4 w-4" />
            Share
          </Button>
          <Button size="sm" className="gap-2">
            <Download className="h-4 w-4" />
            Export PDF
          </Button>
        </div>
      </div>
    </div>
  )
}
