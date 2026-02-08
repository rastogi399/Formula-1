use anchor_lang::prelude::*;

declare_id!("SessioNXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX");

#[program]
pub mod session_keys {
    use super::*;

    /// Create a new session key with spending limits
    pub fn create_session_key(
        ctx: Context<CreateSessionKey>,
        session_pubkey: Pubkey,
        max_amount_per_tx: u64,
        max_total_amount: u64,
        expiry_timestamp: i64,
        allowed_programs: Vec<Pubkey>,
    ) -> Result<()> {
        let session_key = &mut ctx.accounts.session_key;

        session_key.owner = ctx.accounts.owner.key();
        session_key.session_pubkey = session_pubkey;
        session_key.max_amount_per_tx = max_amount_per_tx;
        session_key.max_total_amount = max_total_amount;
        session_key.spent_amount = 0;
        session_key.created_at = Clock::get()?.unix_timestamp;
        session_key.expiry_timestamp = expiry_timestamp;
        session_key.allowed_programs_count = allowed_programs.len() as u8;
        
        // Copy allowed programs into fixed array
        for (i, program) in allowed_programs.iter().enumerate() {
            if i >= 10 {
                break;
            }
            session_key.allowed_programs[i] = *program;
        }
        
        session_key.is_active = true;
        session_key.bump = ctx.bumps.session_key;

        msg!("Session key created: {}", session_pubkey);
        msg!("Max per tx: {}", max_amount_per_tx);
        msg!("Max total: {}", max_total_amount);
        msg!("Expires at: {}", expiry_timestamp);

        Ok(())
    }

    /// Validate session key for a transaction
    pub fn validate_session(
        ctx: Context<ValidateSession>,
        program_id: Pubkey,
        amount: u64,
    ) -> Result<()> {
        let session_key = &mut ctx.accounts.session_key;
        let clock = Clock::get()?;

        // Check if active
        require!(session_key.is_active, ErrorCode::SessionKeyNotActive);

        // Check expiry
        require!(
            clock.unix_timestamp < session_key.expiry_timestamp,
            ErrorCode::SessionKeyExpired
        );

        // Check per-transaction limit
        require!(
            amount <= session_key.max_amount_per_tx,
            ErrorCode::AmountExceedsPerTxLimit
        );

        // Check total limit
        require!(
            session_key.spent_amount + amount <= session_key.max_total_amount,
            ErrorCode::AmountExceedsTotalLimit
        );

        // Check allowed programs
        let mut found = false;
        for i in 0..session_key.allowed_programs_count as usize {
            if session_key.allowed_programs[i] == program_id {
                found = true;
                break;
            }
        }
        require!(found, ErrorCode::ProgramNotAllowed);

        // Update spent amount
        session_key.spent_amount += amount;

        msg!("Session validated - Amount: {}", amount);
        msg!("Total spent: {}", session_key.spent_amount);

        Ok(())
    }

    /// Revoke session key
    pub fn revoke_session_key(ctx: Context<UpdateSessionKey>) -> Result<()> {
        let session_key = &mut ctx.accounts.session_key;
        session_key.is_active = false;

        msg!("Session key revoked");
        Ok(())
    }

    /// Update session key limits
    pub fn update_limits(
        ctx: Context<UpdateSessionKey>,
        max_amount_per_tx: u64,
        max_total_amount: u64,
    ) -> Result<()> {
        let session_key = &mut ctx.accounts.session_key;

        session_key.max_amount_per_tx = max_amount_per_tx;
        session_key.max_total_amount = max_total_amount;

        msg!("Limits updated - Per tx: {}, Total: {}", max_amount_per_tx, max_total_amount);
        Ok(())
    }

    /// Close session key account
    pub fn close_session_key(_ctx: Context<CloseSessionKey>) -> Result<()> {
        msg!("Session key closed");
        Ok(())
    }
}

// ============================================
// Account Contexts
// ============================================

#[derive(Accounts)]
#[instruction(session_pubkey: Pubkey)]
pub struct CreateSessionKey<'info> {
    #[account(
        init,
        payer = owner,
        space = 8 + SessionKey::LEN,
        seeds = [
            b"session",
            owner.key().as_ref(),
            session_pubkey.as_ref(),
        ],
        bump
    )]
    pub session_key: Account<'info, SessionKey>,

    #[account(mut)]
    pub owner: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ValidateSession<'info> {
    #[account(
        mut,
        seeds = [
            b"session",
            session_key.owner.as_ref(),
            session_key.session_pubkey.as_ref(),
        ],
        bump = session_key.bump,
    )]
    pub session_key: Account<'info, SessionKey>,

    /// The session authority must sign
    pub session_authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct UpdateSessionKey<'info> {
    #[account(
        mut,
        seeds = [
            b"session",
            session_key.owner.as_ref(),
            session_key.session_pubkey.as_ref(),
        ],
        bump = session_key.bump,
        has_one = owner,
    )]
    pub session_key: Account<'info, SessionKey>,

    pub owner: Signer<'info>,
}

#[derive(Accounts)]
pub struct CloseSessionKey<'info> {
    #[account(
        mut,
        seeds = [
            b"session",
            session_key.owner.as_ref(),
            session_key.session_pubkey.as_ref(),
        ],
        bump = session_key.bump,
        has_one = owner,
        close = owner
    )]
    pub session_key: Account<'info, SessionKey>,

    #[account(mut)]
    pub owner: Signer<'info>,
}

// ============================================
// State
// ============================================

#[account]
pub struct SessionKey {
    pub owner: Pubkey,                      // 32
    pub session_pubkey: Pubkey,             // 32
    pub max_amount_per_tx: u64,             // 8
    pub max_total_amount: u64,              // 8
    pub spent_amount: u64,                  // 8
    pub created_at: i64,                    // 8
    pub expiry_timestamp: i64,              // 8
    pub allowed_programs: [Pubkey; 10],     // 32 * 10 = 320
    pub allowed_programs_count: u8,         // 1
    pub is_active: bool,                    // 1
    pub bump: u8,                           // 1
}

impl SessionKey {
    pub const LEN: usize = 32 + 32 + 8 + 8 + 8 + 8 + 8 + (32 * 10) + 1 + 1 + 1;
}

// ============================================
// Errors
// ============================================

#[error_code]
pub enum ErrorCode {
    #[msg("Session key is not active")]
    SessionKeyNotActive,

    #[msg("Session key has expired")]
    SessionKeyExpired,

    #[msg("Amount exceeds per-transaction limit")]
    AmountExceedsPerTxLimit,

    #[msg("Amount exceeds total spending limit")]
    AmountExceedsTotalLimit,

    #[msg("Program is not in allowed list")]
    ProgramNotAllowed,
}
