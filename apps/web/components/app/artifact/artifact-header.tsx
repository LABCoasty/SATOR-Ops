"use client"

import { FileOutput, Download, Share2, Printer, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export function ArtifactHeader() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-accent/20">
            <FileOutput className="h-6 w-6 text-accent" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">Decision Artifact</h1>
              <span className="rounded bg-success/20 px-2 py-0.5 text-xs font-medium text-success">Complete</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Generated: Jan 17, 2026 at 14:41:00 UTC · ID: ART-2026-0117-001
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2 bg-transparent">
            <Printer className="h-4 w-4" />
            <span className="hidden sm:inline">Print</span>
          </Button>
          <Button variant="outline" size="sm" className="gap-2 bg-transparent">
            <Share2 className="h-4 w-4" />
            <span className="hidden sm:inline">Share</span>
          </Button>
          <Button variant="outline" size="sm" className="gap-2 bg-transparent">
            <Download className="h-4 w-4" />
            Export PDF
          </Button>
          <Button asChild size="sm" className="gap-2">
            <Link href="/app/receipt">
              <CheckCircle className="h-4 w-4" />
              View Trust Receipt
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
