export default function DecisionPage() {
  return (
    <div className="p-8 mode-decision">
      <h1 className="text-2xl font-bold text-[hsl(var(--decision))]">
        Decision Mode
      </h1>
      <p className="text-muted-foreground mt-2">
        Formal commitment - bounded actions with timeboxed accountability
      </p>
      {/* TODO: Build during hackathon
        - Decision Card Stack UI
        - Decision Clock timer
        - Allowed actions panel (2-3 max)
        - Uncertainty panel
        - Persistent "DECISION MODE ACTIVE" banner
      */}
    </div>
  );
}
