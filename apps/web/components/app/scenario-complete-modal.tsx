"use client"

import { useState } from "react"
import {
  CheckCircle,
  X,
  FileText,
  Shield,
  ExternalLink,
  Trophy,
  Clock,
  Target,
  MessageSquare,
  ArrowRight,
  Loader2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import Link from "next/link"

interface ScenarioCompleteModalProps {
  scenarioId: string
  scenarioName: string
  trustScore: number
  decisionsCount: number
  eventsCount: number
  duration: number
  onClose: () => void
  onAnchor?: () => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function ScenarioCompleteModal({
  scenarioId,
  scenarioName,
  trustScore,
  decisionsCount,
  eventsCount,
  duration,
  onClose,
  onAnchor,
}: ScenarioCompleteModalProps) {
  const [isAnchoring, setIsAnchoring] = useState(false)
  const [isAnchored, setIsAnchored] = useState(false)
  const [txHash, setTxHash] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnchor = async () => {
    setIsAnchoring(true)
    setError(null)
    
    try {
      // Create artifact from scenario
      const artifactResponse = await fetch(`${API_URL}/api/scenarios/${scenarioId}/generate-artifact`, {
        method: "POST",
      })
      
      if (!artifactResponse.ok) {
        throw new Error("Failed to generate artifact")
      }
      
      const artifact = await artifactResponse.json()
      
      // Anchor the artifact
      const anchorResponse = await fetch(`${API_URL}/api/artifacts/${artifact.artifact_id}/anchor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: true }),
      })
      
      const anchorResult = await anchorResponse.json()
      
      if (anchorResult.success) {
        setIsAnchored(true)
        setTxHash(anchorResult.tx_hash)
        onAnchor?.()
      } else {
        throw new Error(anchorResult.error || "Anchor failed")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to anchor")
    } finally {
      setIsAnchoring(false)
    }
  }

  const getTrustScoreColor = (score: number) => {
    if (score >= 0.85) return "text-success"
    if (score >= 0.7) return "text-warning"
    return "text-destructive"
  }

  const getTrustScoreLabel = (score: number) => {
    if (score >= 0.85) return "High Confidence"
    if (score >= 0.7) return "Medium Confidence"
    return "Low Confidence"
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-lg bg-card border border-border rounded-lg shadow-xl animate-in fade-in zoom-in duration-300">
        {/* Success Header */}
        <div className="relative overflow-hidden rounded-t-lg bg-gradient-to-r from-success/20 to-primary/20 px-6 py-8 text-center">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(34,197,94,0.2),transparent)]" />
          <div className="relative">
            <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-success/20 flex items-center justify-center">
              <CheckCircle className="h-8 w-8 text-success" />
            </div>
            <h2 className="text-xl font-bold">Scenario Complete!</h2>
            <p className="text-sm text-muted-foreground mt-1">{scenarioName}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 right-4"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4 p-6 border-b border-border">
          {/* Trust Score */}
          <div className="col-span-2 rounded-lg bg-muted/50 p-4 text-center">
            <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Trust Score</p>
            <p className={cn("text-4xl font-bold font-mono", getTrustScoreColor(trustScore))}>
              {trustScore.toFixed(2)}
            </p>
            <p className={cn("text-sm", getTrustScoreColor(trustScore))}>
              {getTrustScoreLabel(trustScore)}
            </p>
          </div>

          {/* Decisions */}
          <div className="rounded-lg bg-muted/50 p-3 text-center">
            <MessageSquare className="h-5 w-5 text-primary mx-auto mb-1" />
            <p className="text-2xl font-bold">{decisionsCount}</p>
            <p className="text-xs text-muted-foreground">Decisions Made</p>
          </div>

          {/* Events */}
          <div className="rounded-lg bg-muted/50 p-3 text-center">
            <Target className="h-5 w-5 text-primary mx-auto mb-1" />
            <p className="text-2xl font-bold">{eventsCount}</p>
            <p className="text-xs text-muted-foreground">Events Captured</p>
          </div>

          {/* Duration */}
          <div className="col-span-2 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>Completed in {duration.toFixed(0)}s</span>
          </div>
        </div>

        {/* Actions */}
        <div className="p-6 space-y-4">
          {/* Anchor Status */}
          {isAnchored ? (
            <div className="rounded-lg bg-success/10 border border-success/30 p-4">
              <div className="flex items-center gap-3">
                <Shield className="h-6 w-6 text-success" />
                <div>
                  <p className="font-semibold text-success">Anchored to Blockchain</p>
                  <p className="text-xs text-muted-foreground">
                    TX: {txHash?.slice(0, 20)}...
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-3 w-full gap-2"
                onClick={() => window.open(`https://explorer.solana.com/tx/${txHash}?cluster=devnet`, "_blank")}
              >
                <ExternalLink className="h-4 w-4" />
                View on Solana Explorer
              </Button>
            </div>
          ) : error ? (
            <div className="rounded-lg bg-destructive/10 border border-destructive/30 p-4 text-center">
              <p className="text-sm text-destructive">{error}</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={handleAnchor}
              >
                Try Again
              </Button>
            </div>
          ) : (
            <Button
              onClick={handleAnchor}
              disabled={isAnchoring}
              className="w-full gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            >
              {isAnchoring ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Anchoring to Solana...
                </>
              ) : (
                <>
                  <Shield className="h-4 w-4" />
                  Anchor to Blockchain
                </>
              )}
            </Button>
          )}

          {/* View Artifact */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1 gap-2"
              asChild
            >
              <Link href="/app/artifact">
                <FileText className="h-4 w-4" />
                View Artifact
              </Link>
            </Button>
            <Button
              variant="outline"
              className="flex-1 gap-2"
              asChild
            >
              <Link href="/app/decision">
                <ArrowRight className="h-4 w-4" />
                Decision Page
              </Link>
            </Button>
          </div>

          {/* Skip for now */}
          {!isAnchored && (
            <p className="text-center text-xs text-muted-foreground">
              <button className="underline hover:text-foreground" onClick={onClose}>
                Skip and anchor later
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
