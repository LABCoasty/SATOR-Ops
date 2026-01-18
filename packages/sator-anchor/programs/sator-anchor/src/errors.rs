use anchor_lang::prelude::*;

#[error_code]
pub enum SatorAnchorError {
    #[msg("Unauthorized: Only the operator can modify this anchor")]
    Unauthorized,
    
    #[msg("Anchor already exists for this incident")]
    AnchorAlreadyExists,
    
    #[msg("Invalid operator role")]
    InvalidOperatorRole,
    
    #[msg("Packet URI too long (max 200 characters)")]
    PacketUriTooLong,
    
    #[msg("Event count overflow")]
    EventCountOverflow,
    
    #[msg("Anchor requires supervisor approval")]
    RequiresApproval,
    
    #[msg("Only supervisors or admins can approve")]
    NotSupervisorOrAdmin,
    
    #[msg("Anchor is already approved")]
    AlreadyApproved,
    
    #[msg("Invalid hash provided")]
    InvalidHash,
}
