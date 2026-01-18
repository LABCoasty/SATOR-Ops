use anchor_lang::prelude::*;

/// Emitted when a new incident anchor is created
#[event]
pub struct AnchorCreated {
    pub incident_id: u64,
    pub operator: Pubkey,
    pub operator_role: u8,
    pub bundle_root_hash: [u8; 32],
    pub packet_uri: String,
    pub timestamp: i64,
}

/// Emitted when an event is appended to the chain
#[event]
pub struct EventAppended {
    pub incident_id: u64,
    pub event_hash: [u8; 32],
    pub new_chain_head: [u8; 32],
    pub event_count: u32,
    pub timestamp: i64,
}

/// Emitted when artifact hashes are updated
#[event]
pub struct ArtifactsUpdated {
    pub incident_id: u64,
    pub operator: Pubkey,
    pub old_bundle_root: [u8; 32],
    pub new_bundle_root: [u8; 32],
    pub packet_uri: String,
    pub timestamp: i64,
}

/// Emitted when a supervisor approves an anchor
#[event]
pub struct AnchorApproved {
    pub incident_id: u64,
    pub operator: Pubkey,
    pub supervisor: Pubkey,
    pub timestamp: i64,
}
