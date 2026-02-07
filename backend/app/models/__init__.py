"""
Schumacher - Database Models
SQLAlchemy ORM models for PostgreSQL database
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    DECIMAL,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    """User model - stores wallet addresses and preferences"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    wallet_address = Column(String(44), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    display_name = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # User preferences (JSONB for flexibility)
    preferences = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    automations = relationship("Automation", back_populates="user", cascade="all, delete-orphan")
    portfolio_snapshots = relationship("PortfolioSnapshot", back_populates="user", cascade="all, delete-orphan")
    session_keys = relationship("SessionKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.wallet_address}>"


class Transaction(Base):
    """Transaction model - stores all wallet transactions with AI reasoning"""

    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    action = Column(String(50), nullable=False, index=True)  # 'swap', 'send', 'stake', etc.
    source_token = Column(String(44), nullable=True)  # Token mint address
    dest_token = Column(String(44), nullable=True)
    amount_in = Column(DECIMAL(20, 8), nullable=True)
    amount_out = Column(DECIMAL(20, 8), nullable=True)
    price_at_execution = Column(DECIMAL(20, 8), nullable=True)
    gas_fee = Column(DECIMAL(20, 8), nullable=True)
    
    # Status tracking
    status = Column(
        Enum("pending", "success", "failed", name="transaction_status"),
        default="pending",
        nullable=False,
        index=True
    )
    tx_signature = Column(String(128), unique=True, nullable=True, index=True)
    
    # AI reasoning (full LangGraph trace)
    ai_reasoning = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    approval_timestamp = Column(DateTime(timezone=True), nullable=True)
    execution_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.action} - {self.status}>"


class Automation(Base):
    """Automation model - stores DCA, recurring swaps, and rebalancing configs"""

    __tablename__ = "automations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Automation configuration
    automation_type = Column(
        Enum("dca", "recurring_swap", "rebalance", "threshold_swap", name="automation_type"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=True)
    source_token = Column(String(44), nullable=False)
    dest_token = Column(String(44), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    frequency_seconds = Column(Integer, nullable=False)  # Interval in seconds
    
    # On-chain vault
    vault_pda = Column(String(44), nullable=True, unique=True, index=True)
    
    # Status tracking
    status = Column(
        Enum("active", "paused", "completed", "cancelled", name="automation_status"),
        default="active",
        nullable=False,
        index=True
    )
    
    # Execution tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    next_execution_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    total_volume_usd = Column(DECIMAL(20, 2), default=0, nullable=False)
    execution_count = Column(Integer, default=0, nullable=False)
    
    # Additional metadata
    extra_data = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="automations")
    executions = relationship("AutomationExecution", back_populates="automation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Automation {self.automation_type} - {self.status}>"


class AutomationExecution(Base):
    """Automation execution log - tracks each execution of an automation"""

    __tablename__ = "automation_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    automation_id = Column(UUID(as_uuid=True), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Execution details
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    input_amount = Column(DECIMAL(20, 8), nullable=False)
    output_amount = Column(DECIMAL(20, 8), nullable=True)
    price_at_execution = Column(DECIMAL(20, 8), nullable=True)
    transaction_hash = Column(String(128), nullable=True, index=True)
    gas_fee = Column(DECIMAL(20, 8), nullable=True)
    
    # Status
    status = Column(
        Enum("success", "failed", name="execution_status"),
        nullable=False,
        index=True
    )
    error_message = Column(Text, nullable=True)
    
    # Relationships
    automation = relationship("Automation", back_populates="executions")

    def __repr__(self):
        return f"<AutomationExecution {self.status} at {self.executed_at}>"


class PortfolioSnapshot(Base):
    """Portfolio snapshot - daily snapshots for historical tracking"""

    __tablename__ = "portfolio_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Portfolio data
    total_value_usd = Column(DECIMAL(20, 2), nullable=False)
    holdings = Column(JSONB, nullable=False)  # Array of {mint, amount, value_usd, allocation_pct}
    
    # Risk metrics
    risk_score = Column(Integer, nullable=True)
    volatility_90d = Column(Float, nullable=True)
    max_drawdown_90d = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="portfolio_snapshots")

    def __repr__(self):
        return f"<PortfolioSnapshot ${self.total_value_usd} at {self.created_at}>"


class SessionKey(Base):
    """Session key - scoped, time-limited transaction approvals"""

    __tablename__ = "session_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session key details
    public_key = Column(String(88), unique=True, nullable=False, index=True)
    max_amount_usd = Column(DECIMAL(20, 2), nullable=False)
    allowed_tokens = Column(ARRAY(String), nullable=False)  # Array of token mint addresses
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    total_spent_usd = Column(DECIMAL(20, 2), default=0, nullable=False)
    transaction_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="session_keys")

    def __repr__(self):
        return f"<SessionKey {self.public_key[:8]}... expires {self.expires_at}>"


class Notification(Base):
    """Notification model - stores user notifications"""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification details
    type = Column(String(50), nullable=False, index=True)  # 'transaction', 'alert', 'automation'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Related transaction (optional)
    related_tx_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    
    # Status
    read = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<Notification {self.type} - {self.title}>"
