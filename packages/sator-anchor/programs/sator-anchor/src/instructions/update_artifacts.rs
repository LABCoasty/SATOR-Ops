use anchor_lang::prelude::*;
use crate::state::IncidentAnchor;
use crate::errors::SatorAnchorError;
use crate::events::ArtifactsUpdated;

#[derive(Accounts)]
pub struct UpdateArtifacts<'info> {
    #[account(
        mut,
        seeds = [b"incident_anchor", anchor.incident_id.to_le_bytes().as_ref()],
        bump = anchor.bump,
        has_one = operator @ SatorAnchorError::Unauthorized
    )]
    pub anchor: Account<'info, IncidentAnchor>,
    
    pub operator: Signer<'info>,
}

pub fn handler(
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
    let anchor = &mut ctx.accounts.anchor;
    let clock = Clock::get()?;
    
    // Validate URI if provided
    if let Some(ref uri) = packet_uri {
        require!(
            uri.len() <= IncidentAnchor::MAX_URI_LEN,
            SatorAnchorError::PacketUriTooLong
        );
    }
    
    let old_bundle_root = anchor.bundle_root_hash;
    
    // Update hashes if provided
    if let Some(hash) = incident_core_hash {
        anchor.incident_core_hash = hash;
    }
    if let Some(hash) = evidence_set_hash {
        anchor.evidence_set_hash = hash;
    }
    if let Some(hash) = contradictions_hash {
        anchor.contradictions_hash = hash;
    }
    if let Some(hash) = trust_receipt_hash {
        anchor.trust_receipt_hash = hash;
    }
    if let Some(hash) = operator_decisions_hash {
        anchor.operator_decisions_hash = hash;
    }
    if let Some(hash) = timeline_hash {
        anchor.timeline_hash = hash;
    }
    if let Some(uri) = packet_uri.clone() {
        anchor.packet_uri = uri;
    }
    
    // Recompute bundle root
    anchor.bundle_root_hash = anchor.compute_bundle_root();
    
    // Append the change event to the event chain
    let new_head = anchor.compute_new_event_head(&change_event_hash);
    anchor.event_chain_head = new_head;
    anchor.event_count = anchor.event_count
        .checked_add(1)
        .ok_or(SatorAnchorError::EventCountOverflow)?;
    anchor.updated_at = clock.unix_timestamp;
    
    // Emit event
    emit!(ArtifactsUpdated {
        incident_id: anchor.incident_id,
        operator: ctx.accounts.operator.key(),
        old_bundle_root,
        new_bundle_root: anchor.bundle_root_hash,
        packet_uri: anchor.packet_uri.clone(),
        timestamp: clock.unix_timestamp,
    });
    
    msg!(
        "Artifacts updated. Old root: {:?}, New root: {:?}", 
        old_bundle_root, 
        anchor.bundle_root_hash
    );
    
    Ok(())
}
