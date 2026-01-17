import Link from "next/link"
import { Shield } from "lucide-react"

export function LandingFooter() {
  return (
    <footer className="border-t border-border py-12">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <span className="font-semibold">NexHacks</span>
          </div>
          <p className="text-sm text-muted-foreground">
            Operator-grade decision infrastructure for mission-critical operations.
          </p>
          <Link href="/app" className="text-sm text-primary hover:underline">
            Enter Platform →
          </Link>
        </div>
      </div>
    </footer>
  )
}
