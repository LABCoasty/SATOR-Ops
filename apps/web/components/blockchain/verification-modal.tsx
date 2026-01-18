"use client"

import { useState, useEffect } from "react"
import {
  X,
  ShieldCheck,
  ShieldAlert,
  ExternalLink,
  Copy,
  Check,
  Loader2,
  Link2,
  User,
  Clock,
  Hash,
  FileText,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface VerificationModalProps {
  artifactId: string
  incidentId: string
  onClose: () => void
}

interface VerificationData {
  verified: boolean
  incident_id: string
  artifact_id: string
  mismatches: Array<{ field: string; on_chain: string; computed: string }>
  on_chain_data: {
    bundle_root_hash: string
    tx_hash: string
    status: string
    operator: string
    created_at: string
  } | null
  computed_hashes: Record<string, string> | null
  explorer_url: string | null
  timestamp: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function VerificationModal({ artifactId, incidentId, onClose }: VerificationModalProps) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<VerificationData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)

  useEffect(() => {
    fetchVerification()
  }, [artifactId])

  const fetchVerification = async () => {
    try {
      const response = await fetch(`${API_URL}/api/artifacts/${artifactId}/verify`)
      if (response.ok) {
        const result = await response.json()
        setData(result)
      } else {
        setError("Failed to verify artifact")
      }
    } catch {
      setError("Network error")
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(field)
    setTimeout(() => setCopied(null), 2000)
  }

  const hashFields = [
    { key: "incident_core_hash", label: "Incident Core" },
    { key: "evidence_set_hash", label: "Evidence Set" },
    { key: "contradictions_hash", label: "Contradictions" },
    { key: "trust_receipt_hash", label: "Trust Receipt" },
    { key: "operator_decisions_hash", label: "Operator Decisions" },
    { key: "timeline_hash", label: "Timeline" },
    { key: "bundle_root_hash", label: "Bundle Root" },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl max-h-[90vh] overflow-auto bg-card border border-border rounded-lg shadow-xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card px-6 py-4">
          <div className="flex items-center gap-3">
            <div className={cn(
              "h-10 w-10 rounded-full flex items-center justify-center",
              data?.verified ? "bg-success/20" : "bg-destructive/20"
            )}>
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              ) : data?.verified ? (
                <ShieldCheck className="h-5 w-5 text-success" />
              ) : (
                <ShieldAlert className="h-5 w-5 text-destructive" />
              )}
            </div>
            <div>
              <h2 className="font-semibold">Blockchain Verification</h2>
              <p className="text-xs text-muted-foreground">
                Artifact {artifactId.slice(0, 8)}...
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <ShieldAlert className="h-12 w-12 text-destructive mx-auto mb-4" />
              <p className="text-destructive">{error}</p>
            </div>
          ) : data ? (
            <>
              {/* Status Banner */}
              <div className={cn(
                "rounded-lg p-4 flex items-center gap-4",
                data.verified 
                  ? "bg-success/10 border border-success/30" 
                  : "bg-destructive/10 border border-destructive/30"
              )}>
                {data.verified ? (
                  <ShieldCheck className="h-8 w-8 text-success" />
                ) : (
                  <ShieldAlert className="h-8 w-8 text-destructive" />
                )}
                <div>
                  <h3 className={cn(
                    "font-semibold",
                    data.verified ? "text-success" : "text-destructive"
                  )}>
                    {data.verified ? "Verification Successful" : "Verification Failed"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {data.verified 
                      ? "All hashes match on-chain data. Artifact integrity confirmed."
                      : `${data.mismatches.length} hash mismatch(es) detected. Artifact may have been modified.`}
                  </p>
                </div>
              </div>

              {/* On-Chain Data */}
              {data.on_chain_data && (
                <div className="rounded-lg border border-border p-4 space-y-4">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Link2 className="h-4 w-4 text-primary" />
                    On-Chain Data
                  </h3>
                  
                  <div className="grid gap-3">
                    {/* Transaction Hash */}
                    <div className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Hash className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">Transaction</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <code className="text-xs font-mono">
                          {data.on_chain_data.tx_hash.slice(0, 16)}...
                        </code>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => copyToClipboard(data.on_chain_data!.tx_hash, "tx")}
                        >
                          {copied === "tx" ? (
                            <Check className="h-3 w-3 text-success" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                    </div>

                    {/* Operator */}
                    <div className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">Operator</span>
                      </div>
                      <span className="text-sm font-mono">{data.on_chain_data.operator}</span>
                    </div>

                    {/* Timestamp */}
                    <div className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">Anchored At</span>
                      </div>
                      <span className="text-sm">
                        {new Date(data.on_chain_data.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Hash Verification Table */}
              <div className="rounded-lg border border-border p-4 space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  Hash Verification
                </h3>
                
                <div className="space-y-2">
                  {hashFields.map(({ key, label }) => {
                    const mismatch = data.mismatches.find(m => m.field === key)
                    const hash = data.computed_hashes?.[key] || "N/A"
                    
                    return (
                      <div
                        key={key}
                        className={cn(
                          "flex items-center justify-between rounded-md px-3 py-2",
                          mismatch ? "bg-destructive/10" : "bg-success/10"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          {mismatch ? (
                            <ShieldAlert className="h-4 w-4 text-destructive" />
                          ) : (
                            <ShieldCheck className="h-4 w-4 text-success" />
                          )}
                          <span className="text-sm">{label}</span>
                        </div>
                        <code className="text-xs font-mono text-muted-foreground">
                          {hash.slice(0, 12)}...
                        </code>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Mismatches Detail */}
              {data.mismatches.length > 0 && (
                <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 space-y-3">
                  <h3 className="font-semibold text-destructive flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4" />
                    Mismatches Detected
                  </h3>
                  <div className="space-y-2">
                    {data.mismatches.map((m, i) => (
                      <div key={i} className="rounded-md bg-background p-3 space-y-1">
                        <p className="text-sm font-medium">{m.field}</p>
                        <p className="text-xs text-muted-foreground">
                          On-chain: <code>{m.on_chain}</code>
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Computed: <code>{m.computed}</code>
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Explorer Link / Demo Notice */}
              <div className="rounded-lg bg-muted/50 border border-border p-4 text-center space-y-3">
                {data.on_chain_data?.tx_hash && (
                  <>
                    <p className="text-xs text-muted-foreground font-mono">
                      TX: {data.on_chain_data.tx_hash}
                    </p>
                    <div className="flex justify-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-2"
                        onClick={() => window.open(`https://explorer.solana.com/tx/${data.on_chain_data!.tx_hash}?cluster=devnet`, "_blank")}
                      >
                        <ExternalLink className="h-4 w-4" />
                        Solana Explorer
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-2"
                        onClick={() => window.open(`https://solscan.io/tx/${data.on_chain_data!.tx_hash}?cluster=devnet`, "_blank")}
                      >
                        <ExternalLink className="h-4 w-4" />
                        Solscan
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Solana Devnet · Artifact hashes are stored on-chain via Memo program
                    </p>
                  </>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
