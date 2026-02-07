"""
Validation Utilities
Centralized validation functions for request data
Follows single responsibility principle
"""

import re
from typing import Optional
from solders.pubkey import Pubkey

from app.core.constants import (
    AutomationType,
    AutomationStatus,
    Pagination,
    TokenDecimals,
)


class ValidationError(Exception):
    """Custom validation error with field name"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_wallet_address(address: str) -> bool:
    """
    Validate Solana wallet address format.
    
    Args:
        address: The wallet address string to validate
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    if not address:
        raise ValidationError("wallet", "Wallet address is required")
    
    try:
        Pubkey.from_string(address)
        return True
    except Exception:
        raise ValidationError("wallet", "Invalid Solana wallet address format")


def validate_token_mint(mint: str) -> bool:
    """
    Validate token mint address.
    
    Args:
        mint: Token mint address or symbol
        
    Returns:
        True if valid
    """
    if not mint:
        raise ValidationError("token", "Token mint is required")
    
    # Common symbols are allowed
    known_symbols = {"SOL", "USDC", "USDT", "RAY", "SRM", "ORCA", "MSOL"}
    if mint.upper() in known_symbols:
        return True
    
    # Otherwise must be valid pubkey
    try:
        Pubkey.from_string(mint)
        return True
    except Exception:
        raise ValidationError("token", f"Invalid token: {mint}")


def validate_amount(amount: float, min_amount: float = 0.0) -> bool:
    """
    Validate transaction amount.
    
    Args:
        amount: The amount to validate
        min_amount: Minimum allowed amount
        
    Returns:
        True if valid
    """
    if amount is None:
        raise ValidationError("amount", "Amount is required")
    
    if amount <= min_amount:
        raise ValidationError("amount", f"Amount must be greater than {min_amount}")
    
    return True


def validate_frequency(frequency_seconds: int) -> bool:
    """
    Validate automation frequency.
    
    Args:
        frequency_seconds: Frequency in seconds
        
    Returns:
        True if valid
    """
    if frequency_seconds is None or frequency_seconds <= 0:
        raise ValidationError("frequency", "Frequency must be a positive integer")
    
    min_frequency = 60  # 1 minute minimum
    max_frequency = 2592000  # 30 days maximum
    
    if frequency_seconds < min_frequency:
        raise ValidationError("frequency", f"Minimum frequency is {min_frequency} seconds")
    
    if frequency_seconds > max_frequency:
        raise ValidationError("frequency", f"Maximum frequency is {max_frequency} seconds")
    
    return True


def validate_automation_type(automation_type: str) -> bool:
    """Validate automation type is supported"""
    valid_types = [t.value for t in AutomationType]
    
    if automation_type not in valid_types:
        raise ValidationError(
            "automation_type",
            f"Invalid type. Must be one of: {', '.join(valid_types)}"
        )
    
    return True


def validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    """
    Validate and sanitize pagination parameters.
    
    Returns:
        Tuple of (validated_limit, validated_offset)
    """
    validated_limit = min(max(1, limit), Pagination.MAX_LIMIT)
    validated_offset = max(0, offset)
    
    return validated_limit, validated_offset


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Strip whitespace and limit length
    sanitized = value.strip()[:max_length]
    
    # Remove any potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    
    return sanitized
