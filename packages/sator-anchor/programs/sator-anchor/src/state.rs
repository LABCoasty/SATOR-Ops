use anchor_lang::prelude::*;

/// Operator roles in the hierarchy
#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq)]
pub enum OperatorRole {
    Employee = 0,
    Supervisor = 1,
    Admin = 2,
}

impl From<u8> for OperatorRole {
    fn from(value: u8) -> Self {
        match value {
            0 => OperatorRole::Employee,
            1 => OperatorRole::Supervisor,
            2 => OperatorRole::Admin,
            _ => OperatorRole::Employee,
        }
    }
}

/// The main anchor account storing artifact hashes and metadata
/// PDA seeds: ["incident_anchor", incident_id.to_le_bytes()]
#[account]
pub struct IncidentAnchor {
    /// The operator who created this anchor
    pub operator: Pubkey,
    
    /// Unique incident identifier
    pub incident_id: u64,
    
    /// SHA-256 hash of incident core data (title, severity, location, etc.)
    pub incident_core_hash: [u8; 32],
    
    /// SHA-256 hash of evidence set (all sensor readings, snapshots)
    pub evidence_set_hash: [u8; 32],
    
    /// SHA-256 hash of contradictions array
    pub contradictions_hash: [u8; 32],
    
    /// SHA-256 hash of trust receipt (score, confidence, reason codes)
    pub trust_receipt_hash: [u8; 32],
    
    /// SHA-256 hash of operator decisions array
    pub operator_decisions_hash: [u8; 32],
    
    /// SHA-256 hash of timeline/replay events
    pub timeline_hash: [u8; 32],
    
    /// Bundle root: SHA-256(concat of all above hashes in order)
    /// This is the master commitment to the entire artifact
    pub bundle_root_hash: [u8; 32],
    
    /// Rolling hash chain for event integrity
    /// Updated as: new_head = SHA-256(prev_head || event_hash)
    pub event_chain_head: [u8; 32],
    
    /// Number of events appended to the chain
    pub event_count: u32,
    
    /// Operator role (0=employee, 1=supervisor, 2=admin)
    pub operator_role: u8,
    
    /// Supervisor who approved this anchor (if employee created)
    pub supervisor: Option<Pubkey>,
    
    /// Whether this anchor requires supervisor approval
    pub requires_approval: bool,
    
    /// Timestamp when approved by supervisor
    pub approval_timestamp: Option<i64>,
    
    /// URI to the full artifact packet (MongoDB doc ID or IPFS CID)
    pub packet_uri: String,
    
    /// Unix timestamp when anchor was created
    pub created_at: i64,
    
    /// Unix timestamp when anchor was last updated
    pub updated_at: i64,
    
    /// PDA bump seed
    pub bump: u8,
}

impl IncidentAnchor {
    /// Calculate space needed for the account
    /// Fixed fields + string with max length
    pub const MAX_URI_LEN: usize = 200;
    
    pub const SPACE: usize = 8 +  // discriminator
        32 +                       // operator
        8 +                        // incident_id
        32 +                       // incident_core_hash
        32 +                       // evidence_set_hash
        32 +                       // contradictions_hash
        32 +                       // trust_receipt_hash
        32 +                       // operator_decisions_hash
        32 +                       // timeline_hash
        32 +                       // bundle_root_hash
        32 +                       // event_chain_head
        4 +                        // event_count
        1 +                        // operator_role
        1 + 32 +                   // supervisor (Option<Pubkey>)
        1 +                        // requires_approval
        1 + 8 +                    // approval_timestamp (Option<i64>)
        4 + Self::MAX_URI_LEN +    // packet_uri (String)
        8 +                        // created_at
        8 +                        // updated_at
        1;                         // bump
    
    /// Compute the bundle root hash from all artifact hashes
    pub fn compute_bundle_root(&self) -> [u8; 32] {
        use anchor_lang::solana_program::hash::hash;
        
        let mut data = Vec::with_capacity(32 * 6);
        data.extend_from_slice(&self.incident_core_hash);
        data.extend_from_slice(&self.evidence_set_hash);
        data.extend_from_slice(&self.contradictions_hash);
        data.extend_from_slice(&self.trust_receipt_hash);
        data.extend_from_slice(&self.operator_decisions_hash);
        data.extend_from_slice(&self.timeline_hash);
        
        hash(&data).to_bytes()
    }
    
    /// Compute new event chain head
    pub fn compute_new_event_head(&self, event_hash: &[u8; 32]) -> [u8; 32] {
        use anchor_lang::solana_program::hash::hash;
        
        let mut data = Vec::with_capacity(64);
        data.extend_from_slice(&self.event_chain_head);
        data.extend_from_slice(event_hash);
        
        hash(&data).to_bytes()
    }
}
