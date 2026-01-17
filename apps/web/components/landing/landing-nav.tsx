import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Shield } from "lucide-react"

export function LandingNav() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <span className="text-lg font-semibold tracking-tight">NexHacks</span>
          </Link>
          <div className="hidden items-center gap-8 md:flex">
            <Link href="#problem" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Problem
            </Link>
            <Link href="#benefits" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Benefits
            </Link>
            <Link href="#industries" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Industries
            </Link>
            <Link href="#trust" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Trust Layer
            </Link>
          </div>
          <Button asChild size="sm">
            <Link href="/app">Enter Platform</Link>
          </Button>
        </div>
      </div>
    </nav>
  )
}
