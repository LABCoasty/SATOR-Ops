export type ArtifactType =
  | "decision_receipt"
  | "deferral_receipt"
  | "escalation_receipt"
  | "legal_posture_packet";

export interface Artifact {
  id: string;
  type: ArtifactType;
  decisionId: string;
  createdAt: string;
  content: Record<string, unknown>;
  hash: string;
  previousHash?: string;
  verified: boolean;
  verifiedAt?: string;
  metadata?: Record<string, unknown>;
}

export interface DecisionReceipt {
  decisionId: string;
  decisionPosture: string;
  allowedActions: string[];
  actionSelected: string;
  uncertaintySnapshot: number;
  evidenceReferences: string[];
  operatorConfirmation: string;
  timestamp: string;
}

export interface LegalPosturePacket {
  packetId: string;
  decisionTimeline: Record<string, unknown>[];
  modeTransitions: Record<string, unknown>[];
  evidenceChain: string[];
  receipts: string[];
  systemConfig: Record<string, unknown>;
  generatedAt: string;
  tamperEvidentHash: string;
}
