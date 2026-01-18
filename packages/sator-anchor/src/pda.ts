import { PublicKey } from "@solana/web3.js";

// Program ID - will be updated after deployment
export const PROGRAM_ID = new PublicKey(
  "SATRopsAnchor11111111111111111111111111111"
);

// Seed prefix for incident anchors
export const INCIDENT_ANCHOR_SEED = "incident_anchor";

/**
 * Derive the PDA for an incident anchor
 * Seeds: ["incident_anchor", incident_id.to_le_bytes()]
 */
export function deriveIncidentAnchorPDA(
  incidentId: number | bigint,
  programId: PublicKey = PROGRAM_ID
): [PublicKey, number] {
  // Convert incident ID to little-endian bytes (u64)
  const idBuffer = Buffer.alloc(8);
  idBuffer.writeBigUInt64LE(BigInt(incidentId));
  
  return PublicKey.findProgramAddressSync(
    [Buffer.from(INCIDENT_ANCHOR_SEED), idBuffer],
    programId
  );
}

/**
 * Get the PDA address without bump
 */
export function getIncidentAnchorAddress(
  incidentId: number | bigint,
  programId: PublicKey = PROGRAM_ID
): PublicKey {
  const [pda] = deriveIncidentAnchorPDA(incidentId, programId);
  return pda;
}

/**
 * Check if an address is a valid incident anchor PDA
 */
export function isValidIncidentAnchorPDA(
  address: PublicKey,
  incidentId: number | bigint,
  programId: PublicKey = PROGRAM_ID
): boolean {
  const expectedAddress = getIncidentAnchorAddress(incidentId, programId);
  return address.equals(expectedAddress);
}
