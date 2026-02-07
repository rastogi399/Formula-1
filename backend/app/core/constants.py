"""
Backend Configuration Constants
Centralized constants to avoid magic numbers and hardcoded values
"""

from enum import Enum


class RiskThresholds:
    """Risk analysis thresholds for portfolio evaluation"""
    CONCENTRATION_WARNING_PCT = 80
    VOLATILITY_WARNING_PCT = 10
    DRAWDOWN_WARNING_PCT = 20
    HEALTHY_RISK_SCORE = 30
    MAX_RISK_SCORE = 100


class AutomationFrequency:
    """Common automation frequencies in seconds"""
    HOURLY = 3600
    DAILY = 86400
    WEEKLY = 604800
    MONTHLY = 2592000


class TokenDecimals:
    """Standard token decimal places"""
    SOL = 9
    USDC = 6
    USDT = 6
    DEFAULT = 6
    
    @classmethod
    def get(cls, symbol: str) -> int:
        return getattr(cls, symbol.upper(), cls.DEFAULT)


class Pagination:
    """API pagination defaults"""
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 100
    DEFAULT_OFFSET = 0


class AutomationType(str, Enum):
    """Supported automation types"""
    DCA = "dca"
    RECURRING_SWAP = "recurring_swap"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    REBALANCE = "rebalance"


class AutomationStatus(str, Enum):
    """Automation lifecycle states"""
    ACTIVE = "active"
    PAUSED = "paused"
    PENDING_DEPLOYMENT = "pending_deployment"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    """Portfolio risk classification levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    
    @classmethod
    def from_score(cls, score: int) -> "RiskLevel":
        """Determine risk level from numeric score (0-100)"""
        if score <= 25:
            return cls.LOW
        elif score <= 50:
            return cls.MEDIUM
        elif score <= 75:
            return cls.HIGH
        return cls.CRITICAL


class SessionKeyDefaults:
    """Default values for session key creation"""
    DEFAULT_EXPIRY_DAYS = 7
    MAX_EXPIRY_DAYS = 30
    DEFAULT_MAX_PER_TX_LAMPORTS = 1_000_000_000  # 1 SOL
    DEFAULT_MAX_TOTAL_LAMPORTS = 10_000_000_000  # 10 SOL


class CacheKeys:
    """Redis cache key prefixes"""
    SESSION = "session"
    TOKEN_PRICE = "token_price"
    PORTFOLIO = "portfolio"
    USER = "user"


class CacheTTL:
    """Cache time-to-live values in seconds"""
    TOKEN_PRICE = 60  # 1 minute
    PORTFOLIO = 300   # 5 minutes
    SESSION = 3600    # 1 hour
