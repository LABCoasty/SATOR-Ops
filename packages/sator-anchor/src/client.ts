import {
  Connection,
  PublicKey,
  Keypair,
  Transaction,
  TransactionInstruction,
  SystemProgram,
  sendAndConfirmTransaction,
} from "@solana/web3.js";
import { sha256, computeArtifactHashes, toHex, hashesEqual } from "./hasher";
import { deriveIncidentAnchorPDA, PROGRAM_ID } from "./pda";
import type {
  DecisionArtifact,
  OnChainAnchor,
  VerificationResult,
  CreateAnchorParams,
  OperatorRole,
  AnchorStatus,
} from "./types";

// Devnet RPC URL
export const DEVNET_RPC = "https://api.devnet.solana.com";

// Explorer URLs
export const getExplorerUrl = (signature: string, cluster = "devnet") =>
  `https://explorer.solana.com/tx/${signature}?cluster=${cluster}`;

export const getSolscanUrl = (signature: string, cluster = "devnet") =>
  `https://solscan.io/tx/${signature}?cluster=${cluster}`;

/**
 * SATOR Anchor Client
 * Handles all interactions with the Solana program
 */
export class SatorAnchorClient {
  private connection: Connection;
  private programId: PublicKey;
  
  constructor(
    rpcUrl: string = DEVNET_RPC,
    programId: PublicKey = PROGRAM_ID
  ) {
    this.connection = new Connection(rpcUrl, "confirmed");
    this.programId = programId;
  }
  
  /**
   * Get connection instance
   */
  getConnection(): Connection {
    return this.connection;
  }
  
  /**
   * Get PDA for an incident
   */
  getAnchorPDA(incidentId: number): [PublicKey, number] {
    return deriveIncidentAnchorPDA(incidentId, this.programId);
  }
  
  /**
   * Check if an anchor exists for an incident
   */
  async anchorExists(incidentId: number): Promise<boolean> {
    const [pda] = this.getAnchorPDA(incidentId);
    const accountInfo = await this.connection.getAccountInfo(pda);
    return accountInfo !== null;
  }
  
  /**
   * Fetch on-chain anchor data
   */
  async fetchAnchor(incidentId: number): Promise<OnChainAnchor | null> {
    const [pda] = this.getAnchorPDA(incidentId);
    const accountInfo = await this.connection.getAccountInfo(pda);
    
    if (!accountInfo) {
      return null;
    }
    
    // Parse account data (simplified - in production use Anchor's IDL)
    return this.parseAnchorData(accountInfo.data);
  }
  
  /**
   * Parse anchor account data
   */
  private parseAnchorData(data: Buffer): OnChainAnchor {
    // Skip 8-byte discriminator
    let offset = 8;
    
    // operator: Pubkey (32 bytes)
    const operator = new PublicKey(data.subarray(offset, offset + 32));
    offset += 32;
    
    // incident_id: u64 (8 bytes)
    const incidentId = data.readBigUInt64LE(offset);
    offset += 8;
    
    // All the hash fields (32 bytes each)
    const incidentCoreHash = new Uint8Array(data.subarray(offset, offset + 32));
    offset += 32;
    const evidenceSetHash = new Uint8Array(data.subarray(offset, offset + 32));
    offset += 32;
    const contradictionsHash = new Uint8Array(data.subarray(offset, offset + 32));
    offset += 32;
    const trustReceiptHash = new Uint8Array(data.subarray(offset, offset + 32));
    offset += 32;
    const operatorDecisionsHash = new Uint8Array(data.subarray(offset, offset + 32));
    offset += 32;
    const timelineHash = new Uint8Array(data.subarray(offset, offset + 32));
    offset += 32;
    const bundleRootHash = new Uint8Array(data.subarray(offset, offset + 32));
    offset += 32;
    const eventChainHead = new Uint8Array(data.subarray(offset, offset + 32));
    offset += 32;
    
    // event_count: u32 (4 bytes)
    const eventCount = data.readUInt32LE(offset);
    offset += 4;
    
    // operator_role: u8 (1 byte)
    const operatorRole = data.readUInt8(offset);
    offset += 1;
    
    // supervisor: Option<Pubkey> (1 + 32 bytes)
    const hasSupervisor = data.readUInt8(offset) === 1;
    offset += 1;
    const supervisor = hasSupervisor
      ? new PublicKey(data.subarray(offset, offset + 32))
      : null;
    offset += 32;
    
    // requires_approval: bool (1 byte)
    const requiresApproval = data.readUInt8(offset) === 1;
    offset += 1;
    
    // approval_timestamp: Option<i64> (1 + 8 bytes)
    const hasApprovalTimestamp = data.readUInt8(offset) === 1;
    offset += 1;
    const approvalTimestamp = hasApprovalTimestamp
      ? data.readBigInt64LE(offset)
      : null;
    offset += 8;
    
    // packet_uri: String (4 bytes length + string)
    const uriLength = data.readUInt32LE(offset);
    offset += 4;
    const packetUri = data.subarray(offset, offset + uriLength).toString("utf-8");
    offset += uriLength;
    
    // Pad to max URI length
    offset += 200 - uriLength;
    
    // created_at: i64 (8 bytes)
    const createdAt = data.readBigInt64LE(offset);
    offset += 8;
    
    // updated_at: i64 (8 bytes)
    const updatedAt = data.readBigInt64LE(offset);
    offset += 8;
    
    // bump: u8 (1 byte)
    const bump = data.readUInt8(offset);
    
    return {
      operator,
      incidentId,
      incidentCoreHash,
      evidenceSetHash,
      contradictionsHash,
      trustReceiptHash,
      operatorDecisionsHash,
      timelineHash,
      bundleRootHash,
      eventChainHead,
      eventCount,
      operatorRole,
      supervisor,
      requiresApproval,
      approvalTimestamp,
      packetUri,
      createdAt,
      updatedAt,
      bump,
    };
  }
  
  /**
   * Verify an artifact against on-chain anchor
   */
  async verifyArtifact(
    incidentId: number,
    artifact: DecisionArtifact
  ): Promise<VerificationResult> {
    const [pda] = this.getAnchorPDA(incidentId);
    const onChainData = await this.fetchAnchor(incidentId);
    
    if (!onChainData) {
      return {
        verified: false,
        incidentId: String(incidentId),
        onChainData: null,
        computedHashes: null,
        mismatches: [{ field: "anchor", onChain: "null", computed: "exists" }],
        timestamp: new Date(),
        explorerUrl: "",
      };
    }
    
    // Compute hashes from artifact
    const computedHashes = computeArtifactHashes(artifact);
    
    // Compare each hash
    const mismatches: VerificationResult["mismatches"] = [];
    
    const comparisons = [
      { field: "incident_core_hash", onChain: onChainData.incidentCoreHash, computed: computedHashes.incident_core_hash },
      { field: "evidence_set_hash", onChain: onChainData.evidenceSetHash, computed: computedHashes.evidence_set_hash },
      { field: "contradictions_hash", onChain: onChainData.contradictionsHash, computed: computedHashes.contradictions_hash },
      { field: "trust_receipt_hash", onChain: onChainData.trustReceiptHash, computed: computedHashes.trust_receipt_hash },
      { field: "operator_decisions_hash", onChain: onChainData.operatorDecisionsHash, computed: computedHashes.operator_decisions_hash },
      { field: "timeline_hash", onChain: onChainData.timelineHash, computed: computedHashes.timeline_hash },
      { field: "bundle_root_hash", onChain: onChainData.bundleRootHash, computed: computedHashes.bundle_root_hash },
    ];
    
    for (const { field, onChain, computed } of comparisons) {
      if (!hashesEqual(onChain, computed)) {
        mismatches.push({
          field,
          onChain: toHex(onChain),
          computed: toHex(computed),
        });
      }
    }
    
    return {
      verified: mismatches.length === 0,
      incidentId: String(incidentId),
      onChainData,
      computedHashes,
      mismatches,
      timestamp: new Date(),
      explorerUrl: `https://explorer.solana.com/address/${pda.toBase58()}?cluster=devnet`,
    };
  }
  
  /**
   * Get anchor status
   */
  async getAnchorStatus(incidentId: number): Promise<AnchorStatus> {
    const anchor = await this.fetchAnchor(incidentId);
    
    if (!anchor) {
      return "not_anchored" as AnchorStatus;
    }
    
    if (anchor.requiresApproval) {
      return "pending_approval" as AnchorStatus;
    }
    
    return "anchored" as AnchorStatus;
  }
}

/**
 * Create a mock client for testing without blockchain
 */
export function createMockClient(): SatorAnchorClient {
  return new SatorAnchorClient(DEVNET_RPC, PROGRAM_ID);
}
