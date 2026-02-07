"""
Schumacher - Pydantic Schemas
Request/Response schemas for API validation and serialization
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================
# Base Schemas
# ============================================

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {}
        }
    )


# ============================================
# User Schemas
# ============================================

class UserBase(BaseSchema):
    """Base user schema"""
    wallet_address: str = Field(..., min_length=32, max_length=44, description="Solana wallet address")
    email: Optional[str] = Field(None, description="User email (optional)")
    display_name: Optional[str] = Field(None, max_length=255, description="Display name")
    
    @field_validator("wallet_address")
    @classmethod
    def validate_wallet_address(cls, v: str) -> str:
        """Validate Solana wallet address format"""
        if not v or len(v) < 32:
            raise ValueError("Invalid Solana wallet address")
        return v


class UserCreate(UserBase):
    """Schema for creating a new user"""
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserUpdate(BaseSchema):
    """Schema for updating user"""
    email: Optional[str] = None
    display_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# Authentication Schemas
# ============================================

class ChallengeRequest(BaseSchema):
    """Request schema for authentication challenge"""
    wallet: str = Field(..., description="Solana wallet address")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "wallet": "7ZJhKjbFuSxCkq8BdTXPsmmU82vK2gVwdQB4EF6L1S3x"
            }
        }
    )


class ChallengeResponse(BaseSchema):
    """Response schema for authentication challenge"""
    message: str = Field(..., description="Message to sign")
    nonce: str = Field(..., description="Unique nonce")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Sign this message to log in to Schumacher: abc123...",
                "nonce": "abc123..."
            }
        }
    )


class VerifySignatureRequest(BaseSchema):
    """Request schema for signature verification"""
    wallet: str = Field(..., description="Solana wallet address")
    message: str = Field(..., description="Original message that was signed")
    signature: str = Field(..., description="Signature from wallet")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "wallet": "7ZJhKjbFuSxCkq8BdTXPsmmU82vK2gVwdQB4EF6L1S3x",
                "message": "Sign this message to log in to Schumacher: abc123...",
                "signature": "3Bv7wF..."
            }
        }
    )


class TokenResponse(BaseSchema):
    """Response schema for authentication token"""
    token: str = Field(..., description="JWT access token")
    wallet: str = Field(..., description="Wallet address")
    expires_at: datetime = Field(..., description="Token expiration time")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGc...",
                "wallet": "7ZJhKjbFuSxCkq8BdTXPsmmU82vK2gVwdQB4EF6L1S3x",
                "expires_at": "2025-11-30T16:30:45Z"
            }
        }
    )


# ============================================
# Transaction Schemas
# ============================================

class TransactionBase(BaseSchema):
    """Base transaction schema"""
    action: str = Field(..., description="Transaction action: swap, send, stake, etc.")
    source_token: Optional[str] = Field(None, description="Source token mint address")
    dest_token: Optional[str] = Field(None, description="Destination token mint address")
    amount_in: Optional[Decimal] = Field(None, description="Input amount")
    amount_out: Optional[Decimal] = Field(None, description="Output amount")


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction"""
    pass


class TransactionResponse(TransactionBase):
    """Schema for transaction response"""
    id: UUID
    user_id: UUID
    status: str = Field(..., description="Transaction status: pending, success, failed")
    tx_signature: Optional[str] = Field(None, description="On-chain transaction signature")
    price_at_execution: Optional[Decimal] = None
    gas_fee: Optional[Decimal] = None
    ai_reasoning: Optional[Dict[str, Any]] = None
    created_at: datetime
    approval_timestamp: Optional[datetime] = None
    execution_timestamp: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseSchema):
    """Schema for paginated transaction list"""
    transactions: List[TransactionResponse]
    total: int
    limit: int
    offset: int


# ============================================
# Automation Schemas
# ============================================

class AutomationBase(BaseSchema):
    """Base automation schema"""
    automation_type: str = Field(..., description="Type: dca, recurring_swap, rebalance, threshold_swap")
    name: Optional[str] = Field(None, max_length=255, description="Automation name")
    source_token: str = Field(..., description="Source token mint address")
    dest_token: str = Field(..., description="Destination token mint address")
    amount: Decimal = Field(..., gt=0, description="Amount per execution")
    frequency_seconds: int = Field(..., gt=0, description="Execution frequency in seconds")
    
    @field_validator("automation_type")
    @classmethod
    def validate_automation_type(cls, v: str) -> str:
        """Validate automation type"""
        allowed = ["dca", "recurring_swap", "rebalance", "threshold_swap"]
        if v not in allowed:
            raise ValueError(f"automation_type must be one of {allowed}")
        return v


class AutomationCreate(AutomationBase):
    """Schema for creating automation"""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AutomationUpdate(BaseSchema):
    """Schema for updating automation"""
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    frequency_seconds: Optional[int] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AutomationResponse(AutomationBase):
    """Schema for automation response"""
    id: UUID
    user_id: UUID
    vault_pda: Optional[str] = None
    status: str = Field(..., description="Status: active, paused, completed, cancelled")
    created_at: datetime
    next_execution_at: Optional[datetime] = None
    last_execution_at: Optional[datetime] = None
    total_volume_usd: Decimal = Field(default=0)
    execution_count: int = Field(default=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class AutomationListResponse(BaseSchema):
    """Schema for automation list"""
    automations: List[AutomationResponse]
    total: int


# ============================================
# Portfolio Schemas
# ============================================

class TokenHolding(BaseSchema):
    """Schema for individual token holding"""
    mint: str = Field(..., description="Token mint address")
    symbol: str = Field(..., description="Token symbol")
    amount: Decimal = Field(..., description="Token amount")
    price_usd: Decimal = Field(..., description="Current price in USD")
    value_usd: Decimal = Field(..., description="Total value in USD")
    allocation_pct: float = Field(..., description="Portfolio allocation percentage")
    pnl_usd: Optional[Decimal] = Field(None, description="Profit/Loss in USD")
    pnl_pct: Optional[float] = Field(None, description="Profit/Loss percentage")


class PortfolioSummary(BaseSchema):
    """Schema for portfolio summary"""
    total_usd: Decimal = Field(..., description="Total portfolio value in USD")
    token_count: int = Field(..., description="Number of different tokens")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PortfolioPerformance(BaseSchema):
    """Schema for portfolio performance metrics"""
    total_pnl_usd: Decimal = Field(..., description="Total profit/loss in USD")
    total_pnl_pct: float = Field(..., description="Total profit/loss percentage")
    realized_gains_usd: Decimal = Field(..., description="Realized gains in USD")
    unrealized_gains_usd: Decimal = Field(..., description="Unrealized gains in USD")
    return_1d_pct: float = Field(..., description="1-day return percentage")
    return_7d_pct: float = Field(..., description="7-day return percentage")
    return_30d_pct: float = Field(..., description="30-day return percentage")


class PortfolioRisk(BaseSchema):
    """Schema for portfolio risk metrics"""
    risk_score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    risk_level: str = Field(..., description="Risk level: low, medium, high, very_high")
    volatility_90d_pct: float = Field(..., description="90-day volatility percentage")
    max_drawdown_90d_pct: float = Field(..., description="90-day maximum drawdown percentage")
    var_95_usd: Decimal = Field(..., description="Value at Risk (95% confidence) in USD")
    concentration_top3_pct: float = Field(..., description="Concentration in top 3 tokens")


class AIInsights(BaseSchema):
    """Schema for AI-generated insights"""
    summary: str = Field(..., description="Summary of portfolio analysis")
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    recommendations: List[str] = Field(default_factory=list, description="AI recommendations")


class PortfolioResponse(BaseSchema):
    """Schema for complete portfolio response"""
    portfolio_summary: PortfolioSummary
    holdings: List[TokenHolding]
    performance: PortfolioPerformance
    risk: PortfolioRisk
    ai_insights: AIInsights


# ============================================
# Chat Schemas
# ============================================

class ChatMessage(BaseSchema):
    """Schema for chat message"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Swap 20 USDC to SOL",
                "session_id": "sess_123"
            }
        }
    )


class ChatResponse(BaseSchema):
    """Schema for chat response"""
    id: str = Field(..., description="Message ID")
    status: str = Field(..., description="Status: processing, awaiting_approval, success, error")
    action: Optional[str] = Field(None, description="Detected action")
    preview: Optional[Dict[str, Any]] = Field(None, description="Transaction preview")
    transaction: Optional[Dict[str, Any]] = Field(None, description="Transaction details for frontend")
    message: Optional[str] = Field(None, description="Text response from AI")
    next_step: Optional[str] = Field(None, description="Next step instruction")
    error: Optional[str] = Field(None, description="Error message if any")


# ============================================
# Session Key Schemas
# ============================================

class SessionKeyCreate(BaseSchema):
    """Schema for creating session key"""
    max_amount_usd: Decimal = Field(..., gt=0, le=10000, description="Maximum spending limit in USD")
    allowed_tokens: List[str] = Field(..., min_length=1, description="List of allowed token mint addresses")
    duration_hours: int = Field(..., gt=0, le=24, description="Session duration in hours")


class SessionKeyResponse(BaseSchema):
    """Schema for session key response"""
    id: UUID
    public_key: str = Field(..., description="Session key public key")
    max_amount_usd: Decimal
    allowed_tokens: List[str]
    expires_at: datetime
    created_at: datetime
    total_spent_usd: Decimal = Field(default=0)
    transaction_count: int = Field(default=0)
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# Error Schemas
# ============================================

class ErrorResponse(BaseSchema):
    """Schema for error responses"""
    error: str = Field(..., description="Error message")
    details: Optional[Any] = Field(None, description="Additional error details")
    status_code: int = Field(..., description="HTTP status code")
    path: Optional[str] = Field(None, description="Request path")


# ============================================
# Health Check Schema
# ============================================

class HealthResponse(BaseSchema):
    """Schema for health check response"""
    status: str = Field(..., description="Service status")
    environment: str = Field(..., description="Environment name")
    version: str = Field(..., description="API version")
    solana_network: str = Field(..., description="Solana network")
