import { createHash } from "crypto";
import type { DecisionArtifact, ArtifactHashes } from "./types";

/**
 * Canonicalize JSON deterministically (RFC 8785 - JSON Canonicalization Scheme)
 * This ensures the same object always produces the same string
 */
export function canonicalize(obj: unknown): string {
  if (obj === null || obj === undefined) {
    return "null";
  }
  
  if (typeof obj === "boolean" || typeof obj === "number") {
    return JSON.stringify(obj);
  }
  
  if (typeof obj === "string") {
    return JSON.stringify(obj);
  }
  
  if (Array.isArray(obj)) {
    const items = obj.map(item => canonicalize(item));
    return "[" + items.join(",") + "]";
  }
  
  if (typeof obj === "object") {
    const keys = Object.keys(obj).sort();
    const pairs = keys
      .filter(key => (obj as Record<string, unknown>)[key] !== undefined)
      .map(key => {
        const value = canonicalize((obj as Record<string, unknown>)[key]);
        return JSON.stringify(key) + ":" + value;
      });
    return "{" + pairs.join(",") + "}";
  }
  
  return JSON.stringify(obj);
}

/**
 * Compute SHA-256 hash of data
 */
export function sha256(data: string | Uint8Array): Uint8Array {
  const hash = createHash("sha256");
  hash.update(typeof data === "string" ? data : Buffer.from(data));
  return new Uint8Array(hash.digest());
}

/**
 * Compute SHA-256 hash and return as hex string
 */
export function sha256Hex(data: string | Uint8Array): string {
  return Buffer.from(sha256(data)).toString("hex");
}

/**
 * Convert Uint8Array to hex string
 */
export function toHex(bytes: Uint8Array): string {
  return Buffer.from(bytes).toString("hex");
}

/**
 * Convert hex string to Uint8Array
 */
export function fromHex(hex: string): Uint8Array {
  return new Uint8Array(Buffer.from(hex, "hex"));
}

/**
 * Compute all hashes for a decision artifact
 */
export function computeArtifactHashes(artifact: DecisionArtifact): ArtifactHashes {
  // Hash each section of the artifact
  const incidentCoreHash = sha256(canonicalize(artifact.incident));
  const evidenceSetHash = sha256(canonicalize(artifact.evidence));
  const contradictionsHash = sha256(canonicalize(artifact.contradictions));
  const trustReceiptHash = sha256(canonicalize(artifact.trust_receipt));
  const operatorDecisionsHash = sha256(canonicalize(artifact.operator_decisions));
  const timelineHash = sha256(canonicalize(artifact.timeline));
  
  // Compute bundle root (concatenate all hashes in order and hash)
  const bundleData = new Uint8Array(32 * 6);
  bundleData.set(incidentCoreHash, 0);
  bundleData.set(evidenceSetHash, 32);
  bundleData.set(contradictionsHash, 64);
  bundleData.set(trustReceiptHash, 96);
  bundleData.set(operatorDecisionsHash, 128);
  bundleData.set(timelineHash, 160);
  const bundleRootHash = sha256(bundleData);
  
  // Initial event hash is the hash of the full artifact
  const initialEventHash = sha256(canonicalize(artifact));
  
  return {
    incident_core_hash: incidentCoreHash,
    evidence_set_hash: evidenceSetHash,
    contradictions_hash: contradictionsHash,
    trust_receipt_hash: trustReceiptHash,
    operator_decisions_hash: operatorDecisionsHash,
    timeline_hash: timelineHash,
    bundle_root_hash: bundleRootHash,
    initial_event_hash: initialEventHash,
  };
}

/**
 * Compute new event chain head
 */
export function computeEventChainHead(
  prevHead: Uint8Array,
  eventHash: Uint8Array
): Uint8Array {
  const data = new Uint8Array(64);
  data.set(prevHead, 0);
  data.set(eventHash, 32);
  return sha256(data);
}

/**
 * Hash an event for appending to the chain
 */
export function hashEvent(event: unknown): Uint8Array {
  return sha256(canonicalize(event));
}

/**
 * Compare two hashes
 */
export function hashesEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}
