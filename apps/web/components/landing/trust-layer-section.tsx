import { Scale, AlertCircle, HelpCircle, FileText } from "lucide-react"

const trustComponents = [
  {
    title: "Evidence Weighting",
    description: "Each data source receives a reliability weight based on historical accuracy and sensor health.",
    icon: Scale,
    code: "weight: 0.85",
  },
  {
    title: "Contradiction Detection",
    description: "When sources disagree, the system flags the conflict and explains the discrepancy.",
    icon: AlertCircle,
    code: "conflicts: 2",
  },
  {
    title: "Uncertainty Exposure",
    description: "Known unknowns are surfaced explicitly—never hidden from operators.",
    icon: HelpCircle,
    code: "gaps: ['sensor_b']",
  },
  {
    title: "Reason Codes",
    description: "Every trust score comes with machine and human-readable reason codes.",
    icon: FileText,
    code: "code: TR_0x12A",
  },
]

export function TrustLayerSection() {
  return (
    <section id="trust" className="py-24 border-t border-border bg-card/30">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight">How Trust Is Computed</h2>
          <p className="mt-4 text-muted-foreground">A transparent methodology for quantifying decision confidence.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {trustComponents.map((component) => (
            <div key={component.title} className="rounded-lg border border-border bg-card p-6 flex gap-4">
              <div className="shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-secondary">
                  <component.icon className="h-5 w-5 text-primary" />
                </div>
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">{component.title}</h3>
                  <code className="rounded bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
                    {component.code}
                  </code>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">{component.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Trust score visualization */}
        <div className="mt-12 mx-auto max-w-xl">
          <div className="rounded-lg border border-border bg-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Composite Trust Score</span>
              <span className="font-mono text-lg font-bold text-primary">0.87</span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div className="h-full w-[87%] rounded-full bg-primary" />
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Low confidence</span>
              <span>High confidence</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
