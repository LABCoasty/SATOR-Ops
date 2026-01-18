"use client"

import { useState, useEffect } from "react"
import { Shield, ShieldCheck, ShieldAlert, ShieldQuestion, Clock, ExternalLink } from "lucide-react"
import { cn } from "@/lib/utils"

type AnchorStatus = "not_anchored" | "pending" | "pending_approval" | "confirmed" | "verified" | "tampered"

interface VerificationBadgeProps {
  artifactId: string
  status?: AnchorStatus
  txHash?: string
  onClick?: () => void
  size?: "sm" | "default" | "lg"
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function VerificationBadge({
  artifactId,
  status: initialStatus,
  txHash,
  onClick,
  size = "default",
}: VerificationBadgeProps) {
  const [status, setStatus] = useState<AnchorStatus>(initialStatus || "not_anchored")
  const [loading, setLoading] = useState(!initialStatus)

  useEffect(() => {
    if (!initialStatus) {
      fetchStatus()
    }
  }, [artifactId, initialStatus])

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/artifacts/${artifactId}/anchor-status`)
      if (response.ok) {
        const data = await response.json()
        setStatus(data.status)
      }
    } catch {
      // Keep default status
    } finally {
      setLoading(false)
    }
  }

  const config = getStatusConfig(status)
  
  const sizeClasses = {
    sm: "text-xs px-2 py-0.5 gap-1",
    default: "text-sm px-2.5 py-1 gap-1.5",
    lg: "text-base px-3 py-1.5 gap-2",
  }

  const iconSizes = {
    sm: "h-3 w-3",
    default: "h-4 w-4",
    lg: "h-5 w-5",
  }

  if (loading) {
    return (
      <div className={cn(
        "inline-flex items-center rounded-md font-medium",
        "bg-muted/50 text-muted-foreground animate-pulse",
        sizeClasses[size]
      )}>
        <Clock className={iconSizes[size]} />
        Checking...
      </div>
    )
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center rounded-md font-medium transition-all",
        "hover:opacity-90 cursor-pointer",
        config.className,
        sizeClasses[size]
      )}
    >
      <config.icon className={iconSizes[size]} />
      <span>{config.label}</span>
      {txHash && status === "confirmed" && (
        <ExternalLink className={cn(iconSizes[size], "opacity-60")} />
      )}
    </button>
  )
}

function getStatusConfig(status: AnchorStatus) {
  switch (status) {
    case "confirmed":
    case "verified":
      return {
        label: "Anchored",
        icon: ShieldCheck,
        className: "bg-success/20 text-success border border-success/30",
      }
    case "pending":
      return {
        label: "Pending",
        icon: Clock,
        className: "bg-primary/20 text-primary border border-primary/30",
      }
    case "pending_approval":
      return {
        label: "Awaiting Approval",
        icon: ShieldQuestion,
        className: "bg-warning/20 text-warning border border-warning/30",
      }
    case "tampered":
      return {
        label: "Tampered!",
        icon: ShieldAlert,
        className: "bg-destructive/20 text-destructive border border-destructive/30",
      }
    default:
      return {
        label: "Not Anchored",
        icon: Shield,
        className: "bg-muted/50 text-muted-foreground border border-border",
      }
  }
}
