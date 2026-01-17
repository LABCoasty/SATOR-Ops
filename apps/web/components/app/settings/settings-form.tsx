"use client"

import { Button } from "@/components/ui/button"
import { Bell, Monitor, Shield, Database, Download } from "lucide-react"

export function SettingsForm() {
  return (
    <div className="space-y-6">
      {/* Display Settings */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <Monitor className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold">Display</h2>
          </div>
        </div>
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Theme</p>
              <p className="text-xs text-muted-foreground">System appearance preference</p>
            </div>
            <select className="rounded-md border border-input bg-background px-3 py-1.5 text-sm">
              <option>Dark</option>
              <option>Light</option>
              <option>System</option>
            </select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Compact Mode</p>
              <p className="text-xs text-muted-foreground">Reduce spacing for more data density</p>
            </div>
            <input type="checkbox" className="h-4 w-4 rounded border-input" />
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold">Notifications</h2>
          </div>
        </div>
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Anomaly Alerts</p>
              <p className="text-xs text-muted-foreground">Notify when anomalies are detected</p>
            </div>
            <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-input" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Contradiction Warnings</p>
              <p className="text-xs text-muted-foreground">Alert on sensor conflicts</p>
            </div>
            <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-input" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Trust Score Changes</p>
              <p className="text-xs text-muted-foreground">Notify on significant score shifts</p>
            </div>
            <input type="checkbox" className="h-4 w-4 rounded border-input" />
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold">Security</h2>
          </div>
        </div>
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Session Timeout</p>
              <p className="text-xs text-muted-foreground">Auto-logout after inactivity</p>
            </div>
            <select className="rounded-md border border-input bg-background px-3 py-1.5 text-sm">
              <option>15 minutes</option>
              <option>30 minutes</option>
              <option>1 hour</option>
              <option>Never</option>
            </select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Audit Logging</p>
              <p className="text-xs text-muted-foreground">Record all user actions</p>
            </div>
            <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-input" />
          </div>
        </div>
      </div>

      {/* Data Settings */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold">Data Sources</h2>
          </div>
        </div>
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Connected Sources</p>
              <p className="text-xs text-muted-foreground">Active telemetry integrations</p>
            </div>
            <span className="font-mono text-sm text-primary">12</span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Data Retention</p>
              <p className="text-xs text-muted-foreground">How long to keep historical data</p>
            </div>
            <select className="rounded-md border border-input bg-background px-3 py-1.5 text-sm">
              <option>30 days</option>
              <option>90 days</option>
              <option>1 year</option>
              <option>Indefinite</option>
            </select>
          </div>
          <Button variant="outline" size="sm" className="gap-2 bg-transparent">
            <Download className="h-4 w-4" />
            Export All Data
          </Button>
        </div>
      </div>
    </div>
  )
}
