"use client"

import { useState } from "react"
import { Link2, Loader2, CheckCircle, Shield } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface AnchorButtonProps {
  artifactId: string
  scenarioId: string
  incidentId: string
  onAnchor?: (result: AnchorResult) => void
  disabled?: boolean
  size?: "sm" | "default" | "lg"
  variant?: "default" | "outline" | "ghost"
}

interface AnchorResult {
  success: boolean
  txHash?: string
  verificationUrl?: string
  error?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function AnchorButton({
  artifactId,
  scenarioId,
  incidentId,
  onAnchor,
  disabled = false,
  size = "default",
  variant = "default",
}: AnchorButtonProps) {
  const [isAnchoring, setIsAnchoring] = useState(false)
  const [isAnchored, setIsAnchored] = useState(false)
  const [txHash, setTxHash] = useState<string | null>(null)

  const handleAnchor = async () => {
    setIsAnchoring(true)
    
    try {
      const response = await fetch(`${API_URL}/api/artifacts/${artifactId}/anchor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: true }),
      })
      
      const result = await response.json()
      
      if (result.success) {
        setIsAnchored(true)
        setTxHash(result.tx_hash)
        onAnchor?.({
          success: true,
          txHash: result.tx_hash,
          verificationUrl: result.verification_url,
        })
      } else {
        onAnchor?.({
          success: false,
          error: result.error || "Failed to anchor",
        })
      }
    } catch (error) {
      onAnchor?.({
        success: false,
        error: error instanceof Error ? error.message : "Network error",
      })
    } finally {
      setIsAnchoring(false)
    }
  }

  if (isAnchored) {
    return (
      <Button
        variant="outline"
        size={size}
        disabled
        className="gap-2 bg-success/10 border-success/50 text-success"
      >
        <CheckCircle className="h-4 w-4" />
        Anchored
      </Button>
    )
  }

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleAnchor}
      disabled={disabled || isAnchoring}
      className={cn(
        "gap-2",
        variant === "default" && "bg-green-500 hover:bg-green-600 text-white"
      )}
    >
      {isAnchoring ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Anchoring...
        </>
      ) : (
        <>
          <Shield className="h-4 w-4" />
          Anchor to Blockchain
        </>
      )}
    </Button>
  )
}
