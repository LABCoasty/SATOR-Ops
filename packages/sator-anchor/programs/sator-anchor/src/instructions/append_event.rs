use anchor_lang::prelude::*;
use crate::state::IncidentAnchor;
use crate::errors::SatorAnchorError;
use crate::events::EventAppended;

#[derive(Accounts)]
pub struct AppendEvent<'info> {
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
    ctx: Context<AppendEvent>,
    event_hash: [u8; 32],
) -> Result<()> {
    let anchor = &mut ctx.accounts.anchor;
    let clock = Clock::get()?;
    
    // Compute new event chain head
    let new_head = anchor.compute_new_event_head(&event_hash);
    
    // Update anchor
    anchor.event_chain_head = new_head;
    anchor.event_count = anchor.event_count
        .checked_add(1)
        .ok_or(SatorAnchorError::EventCountOverflow)?;
    anchor.updated_at = clock.unix_timestamp;
    
    // Emit event
    emit!(EventAppended {
        incident_id: anchor.incident_id,
        event_hash,
        new_chain_head: new_head,
        event_count: anchor.event_count,
        timestamp: clock.unix_timestamp,
    });
    
    msg!("Event appended. New chain head: {:?}, count: {}", new_head, anchor.event_count);
    
    Ok(())
}
