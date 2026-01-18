use anchor_lang::prelude::*;
use crate::state::IncidentAnchor;
use crate::errors::SatorAnchorError;
use crate::events::AnchorCreated;

#[derive(Accounts)]
#[instruction(incident_id: u64)]
pub struct CreateAnchor<'info> {
    #[account(
        init,
        payer = operator,
        space = IncidentAnchor::SPACE,
        seeds = [b"incident_anchor", incident_id.to_le_bytes().as_ref()],
        bump
    )]
    pub anchor: Account<'info, IncidentAnchor>,
    
    #[account(mut)]
    pub operator: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

pub fn handler(
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
    // Validate URI length
    require!(
        packet_uri.len() <= IncidentAnchor::MAX_URI_LEN,
        SatorAnchorError::PacketUriTooLong
    );
    
    // Validate role
    require!(
        operator_role <= 2,
        SatorAnchorError::InvalidOperatorRole
    );
    
    let anchor = &mut ctx.accounts.anchor;
    let clock = Clock::get()?;
    
    // Set all fields
    anchor.operator = ctx.accounts.operator.key();
    anchor.incident_id = incident_id;
    anchor.incident_core_hash = incident_core_hash;
    anchor.evidence_set_hash = evidence_set_hash;
    anchor.contradictions_hash = contradictions_hash;
    anchor.trust_receipt_hash = trust_receipt_hash;
    anchor.operator_decisions_hash = operator_decisions_hash;
    anchor.timeline_hash = timeline_hash;
    anchor.event_chain_head = initial_event_hash;
    anchor.event_count = 1;
    anchor.operator_role = operator_role;
    anchor.supervisor = None;
    anchor.requires_approval = operator_role == 0; // Employees need approval
    anchor.approval_timestamp = None;
    anchor.packet_uri = packet_uri.clone();
    anchor.created_at = clock.unix_timestamp;
    anchor.updated_at = clock.unix_timestamp;
    anchor.bump = ctx.bumps.anchor;
    
    // Compute and set bundle root
    anchor.bundle_root_hash = anchor.compute_bundle_root();
    
    // Emit event
    emit!(AnchorCreated {
        incident_id,
        operator: ctx.accounts.operator.key(),
        operator_role,
        bundle_root_hash: anchor.bundle_root_hash,
        packet_uri,
        timestamp: clock.unix_timestamp,
    });
    
    msg!("Anchor created for incident {} with bundle root {:?}", incident_id, anchor.bundle_root_hash);
    
    Ok(())
}
