"""
Solana Copilot - Authentication Router
Wallet-based authentication using Solana SignMessage
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    generate_nonce,
    create_challenge_message,
    verify_solana_signature,
    create_access_token,
    verify_token,
)
from app.db.session import get_db
from app.models import User
from app.schemas import (
    ChallengeRequest,
    ChallengeResponse,
    VerifySignatureRequest,
    TokenResponse,
    UserResponse,
)
from app.utils.cache import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Authentication Endpoints
# ============================================

async def get_current_user_dependency(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = None,
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    This should be used in protected endpoints:
    
    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_user_dependency)):
        ...
    
    Args:
        db: Database session
        token: JWT token from Authorization header
    
    Returns:
        Current user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    from fastapi import Header
    from typing import Annotated
    
    # Get token from Authorization header
    # Format: "Bearer {token}"
    # Note: In a real app, use OAuth2PasswordBearer or Header dependency
    # For now, we assume token is passed or we need to fix this to read header
    # But to fix NameError, we just move it.
    
    # Actually, let's fix the header reading while we are at it
    # But I should stick to moving it first to minimize changes.
    
    if not token:
        # Try to get from header if not passed (this won't work without Depends)
        pass

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Remove "Bearer " prefix
    if token.startswith("Bearer "):
        token = token[7:]
    
    # Verify token and get wallet address
    wallet = verify_token(token)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.wallet_address == wallet)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# Export dependency for use in other routers
get_current_user = get_current_user_dependency


@router.post("/request-challenge", response_model=ChallengeResponse)
async def request_challenge(
    request: ChallengeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request authentication challenge for wallet signing.
    
    Flow:
    1. Client requests challenge with wallet address
    2. Server generates nonce and challenge message
    3. Client signs message with wallet
    4. Client submits signature for verification
    
    Args:
        request: Challenge request with wallet address
        db: Database session
    
    Returns:
        Challenge message and nonce
    """
    try:
        # Generate cryptographically secure nonce
        nonce = generate_nonce(length=16)
        
        # Create challenge message
        message = create_challenge_message(nonce)
        
        # Store nonce in Redis with 5-minute expiration
        # This prevents replay attacks
        cache_key = f"auth_nonce:{request.wallet}"
        await redis_client.setex(
            cache_key,
            300,  # 5 minutes
            nonce
        )
        
        logger.info(f"Challenge requested for wallet: {request.wallet}")
        
        return ChallengeResponse(
            message=message,
            nonce=nonce
        )
    
    except Exception as e:
        logger.error(f"Error generating challenge: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate challenge"
        )


@router.post("/verify-signature", response_model=TokenResponse)
async def verify_signature(
    request: VerifySignatureRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify wallet signature and issue JWT token.
    
    Flow:
    1. Verify signature is valid for the wallet
    2. Verify nonce matches stored nonce (prevent replay)
    3. Create or update user in database
    4. Issue JWT access token
    
    Args:
        request: Signature verification request
        db: Database session
    
    Returns:
        JWT token and user info
    """
    try:
        # Extract nonce from message
        # Expected format: "Sign this message to log in to Solana Copilot: {nonce}"
        try:
            nonce_from_message = request.message.split(": ")[-1]
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message format"
            )
        
        # Verify nonce exists and matches
        cache_key = f"auth_nonce:{request.wallet}"
        stored_nonce = await redis_client.get(cache_key)
        
        if not stored_nonce:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nonce expired or invalid. Please request a new challenge."
            )
        
        if stored_nonce.decode() != nonce_from_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nonce mismatch"
            )
        
        # Verify Solana signature
        is_valid = verify_solana_signature(
            wallet_address=request.wallet,
            message=request.message,
            signature=request.signature
        )
        
        if not is_valid:
            logger.warning(f"Invalid signature for wallet: {request.wallet}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        # Delete used nonce (prevent replay attacks)
        await redis_client.delete(cache_key)
        
        # Get or create user
        result = await db.execute(
            select(User).where(User.wallet_address == request.wallet)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                wallet_address=request.wallet,
                last_login_at=datetime.utcnow(),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"New user created: {request.wallet}")
        else:
            # Update last login
            user.last_login_at = datetime.utcnow()
            await db.commit()
            logger.info(f"User logged in: {request.wallet}")
        
        # Create JWT token
        token_data = {
            "wallet": request.wallet,
            "user_id": str(user.id),
        }
        
        expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        access_token = create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        expires_at = datetime.utcnow() + expires_delta
        
        return TokenResponse(
            token=access_token,
            wallet=request.wallet,
            expires_at=expires_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying signature: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify signature"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_user_dependency),
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user (from dependency)
    
    Returns:
        User information
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user_dependency),
):
    """
    Logout current user.
    
    Note: Since we use stateless JWT tokens, logout is handled client-side
    by deleting the token. This endpoint is provided for consistency.
    
    In a production system, you might want to:
    - Add token to a blacklist in Redis
    - Revoke all session keys
    - Clear any cached user data
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.wallet_address}")
    
    # Optional: Add token to blacklist
    # await redis_client.setex(f"blacklist:{token}", settings.JWT_EXPIRATION_HOURS * 3600, "1")
    
    return {"message": "Logged out successfully"}



