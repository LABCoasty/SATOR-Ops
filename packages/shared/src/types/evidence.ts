export type EvidenceType = "sensor" | "log" | "operator_note" | "alarm" | "external";

export type TrustLevel = "high" | "medium" | "low" | "conflicting";

export interface Evidence {
  id: string;
  type: EvidenceType;
  source: string;
  value: Record<string, unknown>;
  timestamp: string;
  ingestedAt: string;
  trustLevel: TrustLevel;
  trustScore: number;
  trustReason?: string;
  metadata?: Record<string, unknown>;
  tags?: Record<string, string>;
}

export interface EvidenceConflict {
  id: string;
  evidenceIds: string[];
  conflictType: string;
  description: string;
  severity: number;
  detectedAt: string;
  resolved: boolean;
  resolution?: string;
}
