export type DecisionMode = "observe" | "decision" | "replay";

export type ActionType = "act" | "escalate" | "defer";

export interface Decision {
  id: string;
  mode: DecisionMode;
  createdAt: string;
  updatedAt?: string;
  evidenceIds: string[];
  allowedActions: string[];
  uncertaintyScore: number;
  timeboxSeconds: number;
  timeboxExpiresAt?: string;
  actionTaken?: ActionType;
  actionDetails?: string;
  actionTakenAt?: string;
  operatorId?: string;
  escalatedTo?: string;
  deferReason?: string;
}

export interface DecisionTransition {
  decisionId: string;
  fromMode: DecisionMode;
  toMode: DecisionMode;
  triggeredBy: string;
  timestamp: string;
  reason?: string;
}
