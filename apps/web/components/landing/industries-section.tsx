import { Building2, ShieldAlert, Factory, Train } from "lucide-react"

const industries = [
  {
    name: "Critical Infrastructure",
    description: "Power grids, water systems, telecommunications",
    icon: Building2,
  },
  {
    name: "Public Safety",
    description: "Emergency response, disaster management",
    icon: ShieldAlert,
  },
  {
    name: "Industrial Operations",
    description: "Manufacturing, energy production, mining",
    icon: Factory,
  },
  {
    name: "Transportation",
    description: "Aviation, maritime, rail operations",
    icon: Train,
  },
]

export function IndustriesSection() {
  return (
    <section id="industries" className="py-24 border-t border-border">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight">Built for Mission-Critical Domains</h2>
          <p className="mt-4 text-muted-foreground">Where the cost of a bad decision is measured in more than money.</p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {industries.map((industry) => (
            <div
              key={industry.name}
              className="group rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary/50"
            >
              <industry.icon className="h-8 w-8 text-muted-foreground group-hover:text-primary transition-colors" />
              <h3 className="mt-4 font-semibold">{industry.name}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{industry.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
