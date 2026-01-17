import { SettingsForm } from "@/components/app/settings/settings-form"

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Configure platform preferences and integrations</p>
      </div>

      <SettingsForm />
    </div>
  )
}
