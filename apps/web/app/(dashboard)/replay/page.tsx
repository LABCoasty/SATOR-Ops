export default function ReplayPage() {
  return (
    <div className="p-8 mode-replay">
      <h1 className="text-2xl font-bold text-[hsl(var(--replay))]">
        Replay Mode
      </h1>
      <p className="text-muted-foreground mt-2">
        Truth reconstruction - accountability, audit, and learning
      </p>
      {/* TODO: Build during hackathon
        - Timeline scrubber
        - State transitions view
        - Evidence anchored to timestamps
        - Mode transitions log
      */}
    </div>
  );
}
