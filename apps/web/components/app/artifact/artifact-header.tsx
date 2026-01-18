"use client"

import { useState } from "react"
import { FileOutput, Download, Share2, Printer, CheckCircle, Check, Copy, Loader2, Shield, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { VerificationBadge } from "@/components/blockchain/verification-badge"
import { VerificationModal } from "@/components/blockchain/verification-modal"
import { AnchorButton } from "@/components/blockchain/anchor-button"

export function ArtifactHeader() {
  const [isSharing, setIsSharing] = useState(false)
  const [copied, setCopied] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [showVerification, setShowVerification] = useState(false)
  const [anchorStatus, setAnchorStatus] = useState<"not_anchored" | "confirmed">("not_anchored")
  const [txHash, setTxHash] = useState<string | null>(null)

  const artifactId = "ART-2026-0117-001"
  const incidentId = "INC-2026-0117-001"
  const scenarioId = "scenario1"
  const artifactUrl = typeof window !== "undefined" ? window.location.href : ""

  const handlePrint = () => {
    window.print()
  }

  const handleShare = async () => {
    setIsSharing(true)
    
    const shareData = {
      title: `Decision Artifact - ${artifactId}`,
      text: `View Decision Artifact ${artifactId} - Trust Score: 0.87 (High Confidence)`,
      url: artifactUrl,
    }

    try {
      // Try native share API first (mobile/supported browsers)
      if (navigator.share && navigator.canShare?.(shareData)) {
        await navigator.share(shareData)
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(artifactUrl)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    } catch (error) {
      // If share was cancelled or failed, try clipboard
      if ((error as Error).name !== "AbortError") {
        try {
          await navigator.clipboard.writeText(artifactUrl)
          setCopied(true)
          setTimeout(() => setCopied(false), 2000)
        } catch {
          console.error("Failed to copy to clipboard")
        }
      }
    } finally {
      setIsSharing(false)
    }
  }

  const handleExportPDF = async () => {
    setIsExporting(true)
    
    try {
      // Dynamic import of html2pdf to avoid SSR issues
      const html2pdf = (await import("html2pdf.js")).default

      // Get the main content area
      const element = document.querySelector("main")
      if (!element) {
        throw new Error("Content not found")
      }

      const opt = {
        margin: [10, 10, 10, 10],
        filename: `decision-artifact-${artifactId}.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { 
          scale: 2,
          useCORS: true,
          letterRendering: true,
          backgroundColor: "#0a0a0a"
        },
        jsPDF: { 
          unit: "mm", 
          format: "a4", 
          orientation: "portrait" as const
        },
        pagebreak: { mode: ["avoid-all", "css", "legacy"] }
      }

      await html2pdf().set(opt).from(element).save()
    } catch (error) {
      console.error("PDF export failed:", error)
      // Fallback to print dialog with PDF option
      window.print()
    } finally {
      setIsExporting(false)
    }
  }

  const handleAnchorResult = (result: { success: boolean; txHash?: string }) => {
    if (result.success && result.txHash) {
      setAnchorStatus("confirmed")
      setTxHash(result.txHash)
    }
  }

  return (
    <>
      <div className="rounded-lg border border-border bg-card p-4 print:border-none print:p-0">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-md bg-accent/20 print:bg-gray-200">
              <FileOutput className="h-6 w-6 text-accent print:text-gray-700" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold">Decision Artifact</h1>
                <span className="rounded bg-success/20 px-2 py-0.5 text-xs font-medium text-success print:bg-green-100 print:text-green-800">Complete</span>
                <VerificationBadge 
                  artifactId={artifactId}
                  status={anchorStatus}
                  txHash={txHash || undefined}
                  onClick={() => setShowVerification(true)}
                  size="sm"
                />
              </div>
              <p className="text-sm text-muted-foreground print:text-gray-600">
                Generated: Jan 17, 2026 at 14:41:00 UTC · ID: {artifactId}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 print:hidden">
            <Button 
              variant="outline" 
              size="sm" 
              className="gap-2 bg-transparent"
              onClick={handlePrint}
            >
              <Printer className="h-4 w-4" />
              <span className="hidden sm:inline">Print</span>
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              className="gap-2 bg-transparent"
              onClick={handleShare}
              disabled={isSharing}
            >
              {copied ? (
                <Check className="h-4 w-4 text-success" />
              ) : (
                <Share2 className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">{copied ? "Copied!" : "Share"}</span>
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              className="gap-2 bg-transparent"
              onClick={handleExportPDF}
              disabled={isExporting}
            >
              {isExporting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              {isExporting ? "Exporting..." : "Export PDF"}
            </Button>
            {anchorStatus === "confirmed" ? (
              <Button 
                variant="outline" 
                size="sm" 
                className="gap-2 bg-success/10 border-success/50 text-success"
                onClick={() => setShowVerification(true)}
              >
                <Shield className="h-4 w-4" />
                Verified on Chain
              </Button>
            ) : (
              <AnchorButton
                artifactId={artifactId}
                scenarioId={scenarioId}
                incidentId={incidentId}
                onAnchor={handleAnchorResult}
                size="sm"
              />
            )}
            <Button asChild size="sm" className="gap-2">
              <Link href="/app/receipt">
                <CheckCircle className="h-4 w-4" />
                View Trust Receipt
              </Link>
            </Button>
          </div>
        </div>

        {/* Blockchain Witness Section */}
        {anchorStatus === "confirmed" && (
          <div className="mt-4 pt-4 border-t border-border">
            <div className="flex items-center justify-between rounded-md bg-success/5 border border-success/20 p-3">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-success" />
                <div>
                  <p className="text-sm font-medium text-success">Blockchain Anchored</p>
                  <p className="text-xs text-muted-foreground">
                    TX: {txHash?.slice(0, 24)}... · Solana Devnet
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="gap-1 text-xs"
                onClick={() => setShowVerification(true)}
              >
                Verify Integrity
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Verification Modal */}
      {showVerification && (
        <VerificationModal
          artifactId={artifactId}
          incidentId={incidentId}
          onClose={() => setShowVerification(false)}
        />
      )}
    </>
  )
}
