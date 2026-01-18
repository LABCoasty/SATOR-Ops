import Link from "next/link"

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-24 overflow-hidden" style={{ backgroundColor: '#07080B' }}>
      {/* Video Background with dark overlay */}
      <div className="absolute inset-0 z-0">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="h-full w-full object-cover opacity-60"
        >
          <source src="/data_center.mp4" type="video/mp4" />
        </video>
        {/* Dark gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#07080B]/45 via-[#07080B]/30 to-[#07080B]" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-3xl text-center">
          {/* Headline */}
          <h1
            className="text-balance text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl"
            style={{
              fontFamily: 'var(--font-nav)',
              color: 'var(--textPrimary)'
            }}
          >
            Operator-grade decision infrastructure.
          </h1>

          {/* Subhead */}
          <p
            className="mt-6 text-pretty text-lg leading-relaxed max-w-2xl mx-auto"
            style={{
              fontFamily: 'var(--font-nav)',
              color: 'var(--textSecondary)'
            }}
          >
            Turn incomplete, conflicting telemetry into defensible action—evidence lineage,
            trust scoring, contradictions, and compliance posture generated at the moment you act.
          </p>

          {/* CTAs - Boxy buttons */}
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            {/* Primary CTA - Light fill, dark text */}
            <Link
              href="/app"
              className="rounded-[6px] px-6 py-3 transition-all duration-200 hover:-translate-y-px hover:shadow-[0_6px_16px_rgba(255,255,255,0.1)]"
              style={{
                fontFamily: 'var(--font-nav)',
                fontSize: '15px',
                fontWeight: 600,
                backgroundColor: '#F0F0F2',
                color: '#0A0A0C',
                border: '1px solid rgba(255,255,255,0.1)',
              }}
            >
              Try Demo
            </Link>

            {/* Secondary CTA - Dark fill, white text */}
            <Link
              href="/app/artifact"
              className="rounded-[6px] px-6 py-3 transition-all duration-200 hover:-translate-y-px hover:shadow-[0_6px_16px_rgba(0,0,0,0.3)]"
              style={{
                fontFamily: 'var(--font-nav)',
                fontSize: '15px',
                fontWeight: 600,
                backgroundColor: '#0A0A0C',
                color: 'rgba(255,255,255,0.92)',
                border: '1px solid rgba(255,255,255,0.16)',
              }}
            >
              See Compliance Posture
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
