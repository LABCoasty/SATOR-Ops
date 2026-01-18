import Link from "next/link"
import Image from "next/image"

export function LandingFooter() {
  return (
    <footer className="border-t py-12" style={{ borderColor: 'var(--border0)', backgroundColor: 'var(--bg0)' }}>
      <div className="mx-auto max-w-7xl px-6">
        {/* Main CTA row */}
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row mb-8">
          <p 
            className="text-lg"
            style={{ fontFamily: 'var(--font-nav)', color: 'var(--textSecondary)' }}
          >
            Need an audit-ready trail for the decisions you're making anyway?
          </p>
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
            Start Demo
          </Link>
        </div>

        {/* Footer links */}
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row pt-8" style={{ borderTop: '1px solid var(--border0)' }}>
          <Link href="/" className="flex items-center gap-2">
            <img
              src="/icon/logo.png"
              alt="AI Logo"
              className="w-6 h-6 object-contain rounded-full"
            />
            <span 
              style={{ fontFamily: 'var(--font-nav)', fontSize: '14px', fontWeight: 600, color: 'var(--textSecondary)' }}
            >
              LOGOSYN
            </span>
          </Link>
          <div className="flex items-center gap-6">
            <Link 
              href="/docs" 
              className="text-sm transition-colors hover:text-white"
              style={{ fontFamily: 'var(--font-nav)', color: 'var(--textTertiary)' }}
            >
              Docs
            </Link>
            <Link 
              href="/security" 
              className="text-sm transition-colors hover:text-white"
              style={{ fontFamily: 'var(--font-nav)', color: 'var(--textTertiary)' }}
            >
              Security
            </Link>
            <Link 
              href="/contact" 
              className="text-sm transition-colors hover:text-white"
              style={{ fontFamily: 'var(--font-nav)', color: 'var(--textTertiary)' }}
            >
              Contact
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
