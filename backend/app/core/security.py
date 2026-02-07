"""
Solana Copilot - Security Utilities
JWT token management, SignMessage verification, and cryptographic utilities
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from solders.pubkey import Pubkey
from solders.signature import Signature
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from app.core.config import settings

# Password hashing context (for future use if needed)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================
# JWT Token Management
# ============================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT access token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and extract wallet address.
    
    Args:
        token: JWT token string
    
    Returns:
        Wallet address if valid, None otherwise
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    wallet: str = payload.get("wallet")
    if wallet is None:
        return None
    
    return wallet


# ============================================
# Solana SignMessage Verification
# ============================================

def verify_solana_signature(
    wallet_address: str,
    message: str,
    signature: str
) -> bool:
    """
    Verify Solana wallet signature using Ed25519.
    
    This implements the Solana SignMessage standard where:
    1. User signs a message with their wallet
    2. Backend verifies the signature matches the wallet's public key
    
    Args:
        wallet_address: Solana wallet public key (base58)
        message: Original message that was signed
        signature: Signature from wallet (base58)
    
    Returns:
        True if signature is valid, False otherwise
    
    Example:
        >>> verify_solana_signature(
        ...     "7ZJhKjbFuSxCkq8BdTXPsmmU82vK2gVwdQB4EF6L1S3x",
        ...     "Sign this message to log in: abc123",
        ...     "3Bv7wF..."
        ... )
        True
    """
    try:
        # Parse wallet public key
        pubkey = Pubkey.from_string(wallet_address)
        
        # Parse signature
        sig = Signature.from_string(signature)
        
        # Encode message to bytes
        message_bytes = message.encode('utf-8')
        
        # Verify signature using Ed25519
        # Note: Solana uses Ed25519 signatures
        verify_key = VerifyKey(bytes(pubkey))
        verify_key.verify(message_bytes, bytes(sig))
        
        return True
    
    except (ValueError, BadSignatureError, Exception) as e:
        # Invalid public key, signature, or verification failed
        return False


def verify_solana_signature_nacl(
    wallet_address: str,
    message: str,
    signature: str
) -> bool:
    """
    Alternative implementation using PyNaCl directly.
    
    Args:
        wallet_address: Solana wallet public key (base58)
        message: Original message that was signed
        signature: Signature from wallet (hex or base58)
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        from base58 import b58decode
        
        # Decode public key from base58
        pubkey_bytes = b58decode(wallet_address)
        
        # Decode signature from base58 or hex
        try:
            sig_bytes = b58decode(signature)
        except:
            sig_bytes = bytes.fromhex(signature)
        
        # Create verify key
        verify_key = VerifyKey(pubkey_bytes)
        
        # Verify signature
        message_bytes = message.encode('utf-8')
        verify_key.verify(message_bytes, sig_bytes)
        
        return True
    
    except Exception:
        return False


# ============================================
# Nonce Generation
# ============================================

def generate_nonce(length: int = 32) -> str:
    """
    Generate cryptographically secure random nonce.
    
    Args:
        length: Length of nonce in bytes
    
    Returns:
        Hex-encoded nonce string
    """
    return secrets.token_hex(length)


def create_challenge_message(nonce: str) -> str:
    """
    Create challenge message for wallet signing.
    
    Args:
        nonce: Random nonce
    
    Returns:
        Formatted challenge message
    """
    return f"Sign this message to log in to Solana Copilot: {nonce}"


# ============================================
# Session Key Management
# ============================================

def generate_session_keypair() -> tuple[str, str]:
    """
    Generate a new session keypair for scoped approvals.
    
    Returns:
        Tuple of (public_key, private_key) as base58 strings
    """
    from solders.keypair import Keypair
    
    keypair = Keypair()
    public_key = str(keypair.pubkey())
    # Note: In production, private key should be encrypted
    private_key = bytes(keypair).hex()
    
    return public_key, private_key


def is_session_key_valid(
    session_key_data: Dict[str, Any],
    current_time: datetime
) -> bool:
    """
    Check if session key is still valid.
    
    Args:
        session_key_data: Session key database record
        current_time: Current timestamp
    
    Returns:
        True if valid, False if expired or revoked
    """
    # Check if revoked
    if session_key_data.get("revoked_at"):
        return False
    
    # Check if expired
    expires_at = session_key_data.get("expires_at")
    if expires_at and current_time > expires_at:
        return False
    
    # Check if spending limit exceeded
    max_amount = session_key_data.get("max_amount_usd", 0)
    total_spent = session_key_data.get("total_spent_usd", 0)
    if total_spent >= max_amount:
        return False
    
    return True


# ============================================
# Password Hashing (for future use)
# ============================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# API Key Generation (for developer API)
# ============================================

def generate_api_key() -> str:
    """
    Generate secure API key for developer access.
    
    Returns:
        API key string (format: sc_live_xxx or sc_test_xxx)
    """
    prefix = "sc_live_" if settings.is_production else "sc_test_"
    key = secrets.token_urlsafe(32)
    return f"{prefix}{key}"


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage.
    Only hashed keys should be stored in database.
    
    Args:
        api_key: Plain API key
    
    Returns:
        Hashed API key
    """
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()
