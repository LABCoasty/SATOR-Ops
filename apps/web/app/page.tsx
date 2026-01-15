import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-b from-background to-background/80">
      <div className="max-w-4xl text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-6xl font-bold tracking-tight">
            <span className="text-primary">SATOR</span>
          </h1>
          <p className="text-xl text-muted-foreground">
            Decision Infrastructure for Physical Systems
          </p>
        </div>

        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Formalizing how humans act in the physical world when telemetry can't
          be fully trusted — and making those decisions defensible.
        </p>

        <div className="flex gap-4 justify-center pt-8">
          <Link
            href="/observe"
            className="px-6 py-3 rounded-lg bg-[hsl(var(--observe))] text-white font-medium hover:opacity-90 transition-opacity"
          >
            Observe Mode
          </Link>
          <Link
            href="/decision"
            className="px-6 py-3 rounded-lg bg-[hsl(var(--decision))] text-white font-medium hover:opacity-90 transition-opacity"
          >
            Decision Mode
          </Link>
          <Link
            href="/replay"
            className="px-6 py-3 rounded-lg bg-[hsl(var(--replay))] text-white font-medium hover:opacity-90 transition-opacity"
          >
            Replay Mode
          </Link>
        </div>

        <div className="pt-16 grid grid-cols-3 gap-8 text-left">
          <div className="space-y-2">
            <h3 className="font-semibold text-[hsl(var(--observe))]">Observe</h3>
            <p className="text-sm text-muted-foreground">
              Passive situational awareness with trust indicators and signal
              monitoring.
            </p>
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold text-[hsl(var(--decision))]">Decision</h3>
            <p className="text-sm text-muted-foreground">
              Formal commitment with bounded actions and timeboxed
              accountability.
            </p>
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold text-[hsl(var(--replay))]">Replay</h3>
            <p className="text-sm text-muted-foreground">
              Truth reconstruction for audits, learning, and compliance
              verification.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
