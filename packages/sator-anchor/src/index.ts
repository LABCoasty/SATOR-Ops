// SATOR Ops Solana Anchor Client Library
// Provides tamper-evident blockchain anchoring for decision artifacts

export * from "./types";
export * from "./hasher";
export * from "./pda";
export * from "./client";

// Re-export commonly used functions
export {
  computeArtifactHashes,
  sha256,
  sha256Hex,
  canonicalize,
  toHex,
  fromHex,
  hashesEqual,
} from "./hasher";

export {
  deriveIncidentAnchorPDA,
  getIncidentAnchorAddress,
  PROGRAM_ID,
  INCIDENT_ANCHOR_SEED,
} from "./pda";

export {
  SatorAnchorClient,
  DEVNET_RPC,
  getExplorerUrl,
  getSolscanUrl,
} from "./client";
