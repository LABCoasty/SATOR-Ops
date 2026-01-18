"use client"

import { useState } from "react"
import { Download, Share2, ShieldCheck, Printer, Check, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ReceiptActions() {
  const [isSharing, setIsSharing] = useState(false)
  const [copied, setCopied] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const receiptHash = "0x7a3f...b2c1"
  const receiptUrl = typeof window !== "undefined" ? window.location.href : ""

  const handlePrint = () => {
    window.print()
  }

  const handleShare = async () => {
    setIsSharing(true)
    
    const shareData = {
      title: "Trust Receipt",
      text: `Trust Receipt - Verification hash: ${receiptHash}`,
      url: receiptUrl,
    }

    try {
      if (navigator.share && navigator.canShare?.(shareData)) {
        await navigator.share(shareData)
      } else {
        await navigator.clipboard.writeText(receiptUrl)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    } catch (error) {
      if ((error as Error).name !== "AbortError") {
        try {
          await navigator.clipboard.writeText(receiptUrl)
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
      const html2pdf = (await import("html2pdf.js")).default

      const element = document.querySelector("main")
      if (!element) {
        throw new Error("Content not found")
      }

      const opt = {
        margin: [10, 10, 10, 10],
        filename: `trust-receipt-${Date.now()}.pdf`,
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
      window.print()
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4 print:border-none print:p-0">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground print:text-gray-600">
          <ShieldCheck className="h-4 w-4" />
          <span>This receipt can be independently verified using hash {receiptHash}</span>
        </div>
        <div className="flex items-center gap-2 print:hidden">
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-2 bg-transparent"
            onClick={handlePrint}
          >
            <Printer className="h-4 w-4" />
            Print
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
            {copied ? "Copied!" : "Share"}
          </Button>
          <Button 
            size="sm" 
            className="gap-2"
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
        </div>
      </div>
    </div>
  )
}
