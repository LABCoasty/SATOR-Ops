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
    <section id="benefits" className="py-24" style={{ backgroundColor: 'var(--bg0)' }}>
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 
            className="text-3xl font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-nav)', color: 'var(--textPrimary)' }}
          >
            Measurable Impact
          </h2>
          <p 
            className="mt-4"
            style={{ fontFamily: 'var(--font-nav)', color: 'var(--textSecondary)' }}
          >
            Real improvements for operators making high-stakes decisions.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {benefits.map((benefit) => (
            <div 
              key={benefit.label} 
              className="rounded-[6px] p-6 space-y-4 transition-all duration-200 hover:-translate-y-px hover:shadow-[0_8px_24px_rgba(255,255,255,0.06)]"
              style={{ 
                backgroundColor: '#F5F5F7',
                border: '1px solid rgba(0,0,0,0.08)',
              }}
            >
              <div className="flex items-center justify-between">
                <span 
                  className="text-3xl font-bold"
                  style={{ fontFamily: 'var(--font-nav)', color: '#0A0A0C' }}
                >
                  {benefit.metric}
                </span>
                <benefit.icon className="h-5 w-5" style={{ color: '#6B7280' }} />
              </div>
              <div className="space-y-1">
                <h3 
                  className="font-semibold"
                  style={{ fontFamily: 'var(--font-nav)', color: '#0A0A0C' }}
                >
                  {benefit.label}
                </h3>
                <p 
                  className="text-sm leading-relaxed"
                  style={{ fontFamily: 'var(--font-nav)', color: '#4B5563' }}
                >
                  {benefit.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
