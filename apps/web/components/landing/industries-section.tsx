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
    <section id="industries" className="py-24" style={{ backgroundColor: '#F7F7F9' }}>
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 
            className="text-3xl font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-nav)', color: '#0A0A0C' }}
          >
            Built for Mission-Critical Domains
          </h2>
          <p 
            className="mt-4"
            style={{ fontFamily: 'var(--font-nav)', color: '#4B5563' }}
          >
            Where the cost of a bad decision is measured in more than money.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {industries.map((industry) => (
            <div
              key={industry.name}
              className="group rounded-[6px] p-6 transition-all duration-200 hover:-translate-y-px hover:shadow-[0_8px_24px_rgba(255,255,255,0.06)]"
              style={{ 
                backgroundColor: '#0A0A0C',
                border: '1px solid rgba(255,255,255,0.1)',
              }}
            >
              <industry.icon 
                className="h-8 w-8 transition-colors" 
                style={{ color: 'rgba(255,255,255,0.6)' }}
              />
              <h3 
                className="mt-4 font-semibold"
                style={{ fontFamily: 'var(--font-nav)', color: 'rgba(255,255,255,0.92)' }}
              >
                {industry.name}
              </h3>
              <p 
                className="mt-2 text-sm"
                style={{ fontFamily: 'var(--font-nav)', color: 'rgba(255,255,255,0.6)' }}
              >
                {industry.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
