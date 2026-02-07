"""Session Keys API Endpoints"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/session-keys", tags=["session-keys"])




class SessionKeyCreate(BaseModel):
    """Request to create a session key"""
    name: str = Field(..., min_length=1, max_length=100)
    max_amount_per_tx: float = Field(..., gt=0, description="Max amount per transaction in USD")
    max_total_amount: float = Field(..., gt=0, description="Max total spending limit in USD")
    expires_in_days: int = Field(default=30, ge=1, le=365)
    allowed_programs: List[str] = Field(default_factory=list)


class SessionKeyUpdate(BaseModel):
    """Request to update session key limits"""
    max_amount_per_tx: Optional[float] = Field(None, gt=0)
    max_total_amount: Optional[float] = Field(None, gt=0)


class SessionKeyResponse(BaseModel):
    """Session key response"""
    id: str
    name: str
    public_key: str
    owner_address: str
    max_amount_per_tx: float
    max_total_amount: float
    spent_amount: float
    created_at: datetime
    expires_at: datetime
    is_active: bool
    allowed_programs: List[str]


class SessionKeyListResponse(BaseModel):
    """List of session keys"""
    session_keys: List[SessionKeyResponse]
    total: int


# ============================================
# In-memory storage (replace with database in production)
# ============================================

session_keys_store: dict = {}


# ============================================
# Endpoints
# ============================================

@router.get("", response_model=SessionKeyListResponse)
async def list_session_keys(
    current_user: User = Depends(get_current_user),
):
    """List all session keys for the current user"""
    user_keys = [
        sk for sk in session_keys_store.values()
        if sk["owner_address"] == current_user.wallet_address
    ]
    
    return SessionKeyListResponse(
        session_keys=[SessionKeyResponse(**sk) for sk in user_keys],
        total=len(user_keys),
    )


@router.post("", response_model=SessionKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_session_key(
    data: SessionKeyCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new session key"""
    session_key_id = str(uuid4())
    session_pubkey = f"Sess{session_key_id[:8]}...{session_key_id[-4:]}"
    
    now = datetime.utcnow()
    expires_at = now + timedelta(days=data.expires_in_days)
    
    session_key = {
        "id": session_key_id,
        "name": data.name,
        "public_key": session_pubkey,
        "owner_address": current_user.wallet_address,
        "max_amount_per_tx": data.max_amount_per_tx,
        "max_total_amount": data.max_total_amount,
        "spent_amount": 0.0,
        "created_at": now,
        "expires_at": expires_at,
        "is_active": True,
        "allowed_programs": data.allowed_programs,
    }
    
    session_keys_store[session_key_id] = session_key
    
    return SessionKeyResponse(**session_key)


@router.get("/{session_key_id}", response_model=SessionKeyResponse)
async def get_session_key(
    session_key_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific session key"""
    session_key = session_keys_store.get(session_key_id)
    
    if not session_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session key not found",
        )
    
    if session_key["owner_address"] != current_user.wallet_address:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session key",
        )
    
    return SessionKeyResponse(**session_key)


@router.patch("/{session_key_id}", response_model=SessionKeyResponse)
async def update_session_key(
    session_key_id: str,
    data: SessionKeyUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update session key limits"""
    session_key = session_keys_store.get(session_key_id)
    
    if not session_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session key not found",
        )
    
    if session_key["owner_address"] != current_user.wallet_address:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this session key",
        )
    
    if data.max_amount_per_tx is not None:
        session_key["max_amount_per_tx"] = data.max_amount_per_tx
    if data.max_total_amount is not None:
        session_key["max_total_amount"] = data.max_total_amount
    
    session_keys_store[session_key_id] = session_key
    
    return SessionKeyResponse(**session_key)


@router.post("/{session_key_id}/revoke", response_model=SessionKeyResponse)
async def revoke_session_key(
    session_key_id: str,
    current_user: User = Depends(get_current_user),
):
    """Revoke a session key"""
    session_key = session_keys_store.get(session_key_id)
    
    if not session_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session key not found",
        )
    
    if session_key["owner_address"] != current_user.wallet_address:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this session key",
        )
    
    session_key["is_active"] = False
    session_keys_store[session_key_id] = session_key
    
    return SessionKeyResponse(**session_key)


@router.delete("/{session_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_key(
    session_key_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a session key"""
    session_key = session_keys_store.get(session_key_id)
    
    if not session_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session key not found",
        )
    
    if session_key["owner_address"] != current_user.wallet_address:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this session key",
        )
    
    del session_keys_store[session_key_id]
    return None


@router.post("/{session_key_id}/validate")
async def validate_session_key(
    session_key_id: str,
    program_id: str,
    amount: float,
    current_user: User = Depends(get_current_user),
):
    """Validate if a session key can be used for a transaction"""
    session_key = session_keys_store.get(session_key_id)
    
    if not session_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session key not found",
        )
    
    # Check if active
    if not session_key["is_active"]:
        return {"valid": False, "reason": "Session key is revoked"}
    
    # Check expiry
    if datetime.utcnow() > session_key["expires_at"]:
        return {"valid": False, "reason": "Session key has expired"}
    
    # Check per-tx limit
    if amount > session_key["max_amount_per_tx"]:
        return {"valid": False, "reason": "Amount exceeds per-transaction limit"}
    
    # Check total limit
    if session_key["spent_amount"] + amount > session_key["max_total_amount"]:
        return {"valid": False, "reason": "Amount exceeds total spending limit"}
    
    # Check allowed programs
    if session_key["allowed_programs"] and program_id not in session_key["allowed_programs"]:
        return {"valid": False, "reason": "Program not in allowed list"}
    
    return {
        "valid": True,
        "remaining_per_tx": session_key["max_amount_per_tx"],
        "remaining_total": session_key["max_total_amount"] - session_key["spent_amount"],
    }
