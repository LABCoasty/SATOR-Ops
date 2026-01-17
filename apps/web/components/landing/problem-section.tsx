import { AlertTriangle, Target } from "lucide-react"

export function ProblemSection() {
  return (
    <section id="problem" className="py-24 border-t border-border">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid gap-16 lg:grid-cols-2">
          {/* Left: The Problem */}
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 text-contradiction">
              <AlertTriangle className="h-5 w-5" />
              <span className="text-sm font-medium uppercase tracking-wide">The Problem</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight">Real-World Operations Are Messy</h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <p>
                Operators face contradictory sensor data, missing telemetry, and incomplete information—yet decisions
                must still be made.
              </p>
              <p>
                Traditional systems either hide uncertainty (dangerous) or expose raw data (overwhelming). Neither
                approach produces defensible decisions.
              </p>
              <ul className="space-y-3 pt-2">
                <li className="flex items-start gap-3">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-contradiction shrink-0" />
                  <span>Sensors report conflicting states</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-contradiction shrink-0" />
                  <span>Critical telemetry goes dark at the worst moments</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-contradiction shrink-0" />
                  <span>Decisions happen under time pressure without documentation</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Right: Mission & Vision */}
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 text-primary">
              <Target className="h-5 w-5" />
              <span className="text-sm font-medium uppercase tracking-wide">Our Mission</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight">Defensible, Reviewable Decisions</h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <p>
                NexHacks transforms operational chaos into structured decision artifacts. Every choice comes with
                evidence, trust scores, and reason codes.
              </p>
              <p>
                We don't hide uncertainty—we quantify it. We don't replace operators—we give them audit-ready
                documentation that stands up to review.
              </p>
              <div className="mt-6 rounded-md border border-border bg-card p-4 space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Evidence attached</span>
                  <span className="font-mono text-success">Yes</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Trust score computed</span>
                  <span className="font-mono text-success">Yes</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Contradictions flagged</span>
                  <span className="font-mono text-success">Yes</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Audit trail complete</span>
                  <span className="font-mono text-success">Yes</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
