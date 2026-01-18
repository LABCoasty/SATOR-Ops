use anchor_lang::prelude::*;

pub mod state;
pub mod instructions;
pub mod errors;
pub mod events;

use instructions::*;

declare_id!("SATRopsAnchor11111111111111111111111111111");

#[program]
pub mod sator_anchor {
    use super::*;

    /// Create a new incident anchor on-chain
    /// Only the operator can create anchors for incidents they own
    pub fn create_anchor(
        ctx: Context<CreateAnchor>,
        incident_id: u64,
        incident_core_hash: [u8; 32],
        evidence_set_hash: [u8; 32],
        contradictions_hash: [u8; 32],
        trust_receipt_hash: [u8; 32],
        operator_decisions_hash: [u8; 32],
        timeline_hash: [u8; 32],
        initial_event_hash: [u8; 32],
        operator_role: u8,
        packet_uri: String,
    ) -> Result<()> {
        instructions::create_anchor::handler(
            ctx,
            incident_id,
            incident_core_hash,
            evidence_set_hash,
            contradictions_hash,
            trust_receipt_hash,
            operator_decisions_hash,
            timeline_hash,
            initial_event_hash,
            operator_role,
            packet_uri,
        )
    }

    /// Append an event to the event chain
    /// Updates event_chain_head = sha256(prev_head || event_hash)
    pub fn append_event(
        ctx: Context<AppendEvent>,
        event_hash: [u8; 32],
    ) -> Result<()> {
        instructions::append_event::handler(ctx, event_hash)
    }

    /// Update artifact hashes and recompute bundle root
    /// Used when artifact is modified (e.g., new evidence, decision changes)
    pub fn update_artifacts(
        ctx: Context<UpdateArtifacts>,
        incident_core_hash: Option<[u8; 32]>,
        evidence_set_hash: Option<[u8; 32]>,
        contradictions_hash: Option<[u8; 32]>,
        trust_receipt_hash: Option<[u8; 32]>,
        operator_decisions_hash: Option<[u8; 32]>,
        timeline_hash: Option<[u8; 32]>,
        change_event_hash: [u8; 32],
        packet_uri: Option<String>,
    ) -> Result<()> {
        instructions::update_artifacts::handler(
            ctx,
            incident_core_hash,
            evidence_set_hash,
            contradictions_hash,
            trust_receipt_hash,
            operator_decisions_hash,
            timeline_hash,
            change_event_hash,
            packet_uri,
        )
    }

    /// Supervisor approves an employee's anchor
    pub fn approve_anchor(
        ctx: Context<ApproveAnchor>,
    ) -> Result<()> {
        instructions::approve_anchor::handler(ctx)
    }
}
