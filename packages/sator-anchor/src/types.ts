import { PublicKey } from "@solana/web3.js";

/**
 * Operator role hierarchy
 */
export enum OperatorRole {
  Employee = 0,
  Supervisor = 1,
  Admin = 2,
}

/**
 * Decision Artifact structure matching SATOR Ops output
 */
export interface DecisionArtifact {
  artifact_id: string;
  incident_id: string;
  scenario_id: string;
  scenario_type: string;
  created_at: string;
  
  incident: {
    id: string;
    title: string;
    severity: string;
    location?: string;
    time_window?: {
      start: string;
      end: string;
    };
  };
  
  evidence: Array<{
    id: string;
    source: string;
    sensor_id?: string;
    readings?: any[];
    timestamp: string;
    trust_score?: number;
  }>;
  
  contradictions: Array<{
    id: string;
    type: string;
    severity: string;
    evidence_ids: string[];
    resolution?: string;
  }>;
  
  trust_receipt: {
    receipt_id: string;
    overall_trust_score: number;
    confidence_band: string;
    reason_codes: string[];
    factors: Array<{
      name: string;
      value: number;
      impact: string;
    }>;
  };
  
  operator_decisions: Array<{
    decision_id: string;
    event_id: string;
    time_sec: number;
    title: string;
    description: string;
    severity: string;
    response: string;
    response_time_sec: number;
    explanation?: string;
    recommendation?: string;
    timestamp: string;
  }>;
  
  timeline: Array<{
    event_id: string;
    time_sec: number;
    title: string;
    description: string;
    severity: string;
    requires_decision: boolean;
  }>;
  
  operator: {
    id: string;
    name?: string;
    role: OperatorRole;
    public_key?: string;
  };
}

/**
 * Computed hashes from an artifact
 */
export interface ArtifactHashes {
  incident_core_hash: Uint8Array;
  evidence_set_hash: Uint8Array;
  contradictions_hash: Uint8Array;
  trust_receipt_hash: Uint8Array;
  operator_decisions_hash: Uint8Array;
  timeline_hash: Uint8Array;
  bundle_root_hash: Uint8Array;
  initial_event_hash: Uint8Array;
}

/**
 * On-chain anchor data
 */
export interface OnChainAnchor {
  operator: PublicKey;
  incidentId: bigint;
  incidentCoreHash: Uint8Array;
  evidenceSetHash: Uint8Array;
  contradictionsHash: Uint8Array;
  trustReceiptHash: Uint8Array;
  operatorDecisionsHash: Uint8Array;
  timelineHash: Uint8Array;
  bundleRootHash: Uint8Array;
  eventChainHead: Uint8Array;
  eventCount: number;
  operatorRole: number;
  supervisor: PublicKey | null;
  requiresApproval: boolean;
  approvalTimestamp: bigint | null;
  packetUri: string;
  createdAt: bigint;
  updatedAt: bigint;
  bump: number;
}

/**
 * Verification result
 */
export interface VerificationResult {
  verified: boolean;
  incidentId: string;
  onChainData: OnChainAnchor | null;
  computedHashes: ArtifactHashes | null;
  mismatches: Array<{
    field: string;
    onChain: string;
    computed: string;
  }>;
  timestamp: Date;
  explorerUrl: string;
}

/**
 * Anchor creation parameters
 */
export interface CreateAnchorParams {
  incidentId: number;
  artifact: DecisionArtifact;
  operatorRole: OperatorRole;
  packetUri: string;
}

/**
 * Anchor status
 */
export enum AnchorStatus {
  NotAnchored = "not_anchored",
  PendingApproval = "pending_approval",
  Anchored = "anchored",
  Verified = "verified",
  Tampered = "tampered",
}
