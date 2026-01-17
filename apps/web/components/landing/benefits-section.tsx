import { Clock, Shield, FileCheck, Eye } from "lucide-react"

const benefits = [
  {
    metric: "73%",
    label: "Faster Decisions",
    description: "Structured evidence reduces decision latency under pressure",
    icon: Clock,
  },
  {
    metric: "0.92",
    label: "Trust Score Avg",
    description: "Quantified confidence in every operational decision",
    icon: Shield,
  },
  {
    metric: "100%",
    label: "Audit Ready",
    description: "Every decision produces a reviewable artifact",
    icon: FileCheck,
  },
  {
    metric: "Clear",
    label: "Operator Clarity",
    description: "Surface unknowns instead of hiding them",
    icon: Eye,
  },
]

export function BenefitsSection() {
  return (
    <section id="benefits" className="py-24 border-t border-border bg-card/30">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight">Measurable Impact</h2>
          <p className="mt-4 text-muted-foreground">Real improvements for operators making high-stakes decisions.</p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {benefits.map((benefit) => (
            <div key={benefit.label} className="rounded-lg border border-border bg-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-3xl font-bold text-primary">{benefit.metric}</span>
                <benefit.icon className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <h3 className="font-semibold">{benefit.label}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{benefit.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
