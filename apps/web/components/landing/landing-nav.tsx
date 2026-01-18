import Link from "next/link"

export function LandingNav() {
  return (
    <nav 
      className="fixed top-0 left-0 right-0 z-50 h-16 border-b border-[rgba(255,255,255,0.08)] bg-gradient-to-b from-[#0C0C0E] to-[#0A0A0C] backdrop-blur-md"
    >
      <div className="mx-auto max-w-7xl px-6 h-full">
        <div className="flex items-center justify-between h-full">
          {/* Brand - LOGOSYN */}
          <Link href="/" className="flex items-center">
            <span 
              style={{
                fontFamily: 'var(--font-nav)',
                fontSize: '18px',
                fontWeight: 600,
                letterSpacing: '0.12em',
                textTransform: 'uppercase' as const,
                color: 'rgba(255,255,255,0.95)',
              }}
            >
              LOGOSYN
            </span>
          </Link>

          {/* Menu Items - Centered */}
          <div 
            className="hidden items-center gap-6 md:flex"
            style={{
              fontFamily: 'var(--font-nav)',
              fontSize: '14px',
              fontWeight: 500,
              letterSpacing: '0.02em',
            }}
          >
            <Link 
              href="#problem" 
              className="py-3 transition-colors hover:text-white"
              style={{ color: 'rgba(255,255,255,0.72)' }}
            >
              Problem
            </Link>
            <Link 
              href="#benefits" 
              className="py-3 transition-colors hover:text-white"
              style={{ color: 'rgba(255,255,255,0.72)' }}
            >
              Benefits
            </Link>
            <Link 
              href="#industries" 
              className="py-3 transition-colors hover:text-white"
              style={{ color: 'rgba(255,255,255,0.72)' }}
            >
              Industries
            </Link>
            <Link 
              href="#trust" 
              className="py-3 transition-colors hover:text-white"
              style={{ color: 'rgba(255,255,255,0.72)' }}
            >
              Trust Layer
            </Link>
          </div>

          {/* CTA Button - Boxy */}
          <Link 
            href="/app"
            className="rounded-[6px] px-4 py-2.5 transition-all duration-200 hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(255,255,255,0.12),0_1px_2px_rgba(0,0,0,0.08)]"
            style={{
              fontFamily: 'var(--font-nav)',
              fontSize: '14px',
              fontWeight: 600,
              backgroundColor: '#F0F0F2',
              color: '#0A0A0C',
            }}
          >
            Enter Platform
          </Link>
        </div>
      </div>
    </nav>
  )
}
