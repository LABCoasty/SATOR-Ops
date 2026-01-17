import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Play } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-24 overflow-hidden">
      {/* Subtle grid background */}
      <div className="absolute inset-0 opacity-[0.03]">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `linear-gradient(to right, currentColor 1px, transparent 1px),
                            linear-gradient(to bottom, currentColor 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      <div className="relative mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-3xl text-center">
          {/* Status badge */}
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-border bg-secondary/50 px-4 py-1.5">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
            <span className="text-xs font-medium text-muted-foreground">Operator-Grade Decision Infrastructure</span>
          </div>

          <h1 className="text-balance text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Decisions You Can Defend
          </h1>

          <p className="mt-6 text-pretty text-lg text-muted-foreground leading-relaxed">
            Transform unreliable data into structured decisions with evidence, trust scoring, and audit-ready artifacts.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button asChild size="lg" className="gap-2">
              <Link href="/app">
                Run a Simulation
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="gap-2 bg-transparent">
              <Link href="/app/artifact">
                <Play className="h-4 w-4" />
                View a Decision Packet
              </Link>
            </Button>
          </div>
        </div>

        {/* Preview mockup */}
        <div className="mt-20 mx-auto max-w-5xl">
          <div className="rounded-lg border border-border bg-card p-1">
            <div className="rounded-md bg-muted/30 aspect-[16/9] flex items-center justify-center">
              <div className="text-center space-y-4">
                <div className="inline-flex items-center gap-3 rounded-md border border-border bg-card px-4 py-2">
                  <span className="h-3 w-3 rounded-full bg-success" />
                  <span className="font-mono text-sm">DECISION_READY</span>
                  <span className="text-muted-foreground text-sm">Trust: 0.87</span>
                </div>
                <p className="text-sm text-muted-foreground">Platform interface preview</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
