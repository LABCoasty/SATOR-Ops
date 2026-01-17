"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Shield, Radio, GitBranch, FileOutput, Receipt, Settings, ChevronLeft } from "lucide-react"
import { useState } from "react"

const navItems = [
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
        "flex flex-col border-r border-border bg-sidebar transition-all duration-200",
        collapsed ? "w-16" : "w-56",
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center justify-between border-b border-sidebar-border px-4">
        <Link href="/" className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-sidebar-primary shrink-0" />
          {!collapsed && <span className="font-semibold text-sidebar-foreground">SATOR-Ops</span>}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded hover:bg-sidebar-accent text-sidebar-foreground"
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Bottom Settings */}
      <div className="border-t border-sidebar-border p-2">
        <Link
          href="/app/settings"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground transition-colors"
        >
          <Settings className="h-4 w-4 shrink-0" />
          {!collapsed && <span>Settings</span>}
        </Link>
      </div>
    </aside>
  )
}
