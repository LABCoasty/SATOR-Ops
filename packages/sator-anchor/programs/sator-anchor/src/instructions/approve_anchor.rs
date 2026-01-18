use anchor_lang::prelude::*;
use crate::state::IncidentAnchor;
use crate::errors::SatorAnchorError;
use crate::events::AnchorApproved;

#[derive(Accounts)]
pub struct ApproveAnchor<'info> {
    #[account(
        mut,
        seeds = [b"incident_anchor", anchor.incident_id.to_le_bytes().as_ref()],
        bump = anchor.bump,
    )]
    pub anchor: Account<'info, IncidentAnchor>,
    
    /// The supervisor or admin approving this anchor
    pub approver: Signer<'info>,
}

pub fn handler(ctx: Context<ApproveAnchor>) -> Result<()> {
    let anchor = &mut ctx.accounts.anchor;
    let clock = Clock::get()?;
    
    // Check if already approved
    require!(
        anchor.requires_approval,
        SatorAnchorError::AlreadyApproved
    );
    
    // In a real implementation, we'd verify the approver has supervisor/admin role
    // For now, we trust the caller (backend enforces role checks)
    
    // Mark as approved
    anchor.supervisor = Some(ctx.accounts.approver.key());
    anchor.requires_approval = false;
    anchor.approval_timestamp = Some(clock.unix_timestamp);
    anchor.updated_at = clock.unix_timestamp;
    
    // Emit event
    emit!(AnchorApproved {
        incident_id: anchor.incident_id,
        operator: anchor.operator,
        supervisor: ctx.accounts.approver.key(),
        timestamp: clock.unix_timestamp,
    });
    
    msg!(
        "Anchor for incident {} approved by {:?}", 
        anchor.incident_id, 
        ctx.accounts.approver.key()
    );
    
    Ok(())
}
