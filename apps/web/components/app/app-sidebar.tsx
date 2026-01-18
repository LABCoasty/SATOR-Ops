"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
<<<<<<< HEAD
import { Shield, Radio, GitBranch, FileOutput, Receipt, Settings, ChevronLeft, LucideIcon, Bot } from "lucide-react"
import { useState, ReactNode } from "react"
=======
import { Radio, GitBranch, FileOutput, Receipt, Settings, ChevronLeft } from "lucide-react"
import { useState } from "react"
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)

type NavItem = {
  label: string
  href: string
  icon: LucideIcon
  mode: "ingest" | "decision" | "artifact"
  badge?: ReactNode
}

const navItems: NavItem[] = [
  {
    label: "Data Ingest",
    href: "/app/ingest",
    icon: Radio,
    mode: "ingest" as const,
  },
  {
    label: "Decision / Trust",
    href: "/app/decision",
    icon: GitBranch,
    mode: "decision" as const,
  },
  {
    label: "MCP Agent",
    href: "/app/agent",
    icon: Bot,
    mode: "decision" as const,
    badge: "11 tools",
  },
  {
    label: "Create Artifact",
    href: "/app/artifact",
    icon: FileOutput,
    mode: "artifact" as const,
  },
  {
    label: "Trust Receipt",
    href: "/app/receipt",
    icon: Receipt,
    mode: "artifact" as const,
  },
]

export function AppSidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        "flex flex-col border-r transition-all duration-200",
        collapsed ? "w-16" : "w-56",
      )}
      style={{ 
        backgroundColor: 'var(--bg0)',
        borderColor: 'var(--border0)',
      }}
    >
      {/* Logo - LOGOSYN text only */}
      <div 
        className="flex h-14 items-center justify-between px-4"
        style={{ borderBottom: '1px solid var(--border0)' }}
      >
        <Link href="/" className="flex items-center">
          {!collapsed && (
            <span 
              className="font-bold"
              style={{ 
                fontFamily: 'var(--font-nav)',
                fontSize: '16px',
                fontWeight: 700,
                letterSpacing: '0.08em',
                color: 'var(--textPrimary)',
              }}
            >
              LOGOSYN
            </span>
          )}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded transition-colors"
          style={{ color: 'var(--textSecondary)' }}
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      {/* Navigation - LS16 style: white highlight bar for active */}
      <nav className="flex-1 py-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors mx-0",
                isActive
                  ? "text-black"
                  : "text-white/70 hover:bg-white/5"
              )}
              style={isActive ? { 
                backgroundColor: '#FFFFFF',
                color: '#0A0A0C',
              } : {
                fontFamily: 'var(--font-nav)',
              }}
            >
              <item.icon className="h-4 w-4 shrink-0" />
<<<<<<< HEAD
              {!collapsed && (
                <span className="flex items-center gap-2">
                  {item.label}
                  {item.badge && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/20 text-primary font-medium">
                      {item.badge}
                    </span>
                  )}
                </span>
              )}
=======
              {!collapsed && <span style={{ fontFamily: 'var(--font-nav)' }}>{item.label}</span>}
>>>>>>> 38715be (add ROYGBIV semantic color system for status indicators)
            </Link>
          )
        })}
      </nav>

      {/* Bottom Settings */}
      <div style={{ borderTop: '1px solid var(--border0)' }} className="py-2">
        <Link
          href="/app/settings"
          className="flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors hover:bg-white/5"
          style={{ 
            fontFamily: 'var(--font-nav)',
            color: 'var(--textSecondary)',
          }}
        >
          <Settings className="h-4 w-4 shrink-0" />
          {!collapsed && <span>Settings</span>}
        </Link>
      </div>
    </aside>
  )
}
