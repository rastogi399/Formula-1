"""
Solana Copilot - Core Configuration
Centralized configuration management using Pydantic Settings
"""

import secrets
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and type safety.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ============================================
    # Environment
    # ============================================
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    NODE_ENV: str = Field(default="development")
    
    # ============================================
    # API Configuration
    # ============================================
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_RELOAD: bool = Field(default=True)
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # ============================================
    # Security
    # ============================================
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_HOURS: int = Field(default=24)
    
    # Session Keys
    SESSION_KEY_MAX_DURATION_HOURS: int = Field(default=1)
    SESSION_KEY_MAX_AMOUNT_USD: float = Field(default=1000.0)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)
    
    # ============================================
    # Database (PostgreSQL)
    # ============================================
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/solana_copilot",
        description="PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    
    # Individual components (for Docker)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="solana_copilot")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    
    # ============================================
    # Redis
    # ============================================
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    
    # Cache TTL (seconds)
    CACHE_TTL_PRICES: int = Field(default=300)  # 5 minutes
    CACHE_TTL_PORTFOLIO: int = Field(default=60)  # 1 minute
    CACHE_TTL_BALANCES: int = Field(default=30)  # 30 seconds
    
    # ============================================
    # Celery
    # ============================================
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")
    
    # ============================================
    # Blockchain Selection
    # ============================================
    # Active blockchain: "solana" (hidden) or "ethereum" (shown to UI)
    ACTIVE_CHAIN: str = Field(default="ethereum", description="Active blockchain: solana or ethereum")
    
    # ============================================
    # Solana (Kept for backward compatibility)
    # ============================================
    SOLANA_NETWORK: str = Field(default="devnet", description="mainnet-beta, devnet, testnet")
    SOLANA_RPC_URL: str = Field(default="https://api.devnet.solana.com")
    SOLANA_WS_URL: str = Field(default="wss://api.devnet.solana.com")
    
    # Program IDs (deployed Anchor programs)
    DCA_PROGRAM_ID: Optional[str] = Field(default=None)
    REBALANCE_PROGRAM_ID: Optional[str] = Field(default=None)
    SESSION_KEY_PROGRAM_ID: Optional[str] = Field(default=None)
    
    # ============================================
    # Helius RPC
    # ============================================
    HELIUS_API_KEY: Optional[str] = Field(default=None)
    HELIUS_RPC_URL: Optional[str] = Field(default=None)
    HELIUS_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    
    @property
    def helius_rpc_url_with_key(self) -> str:
        """Get Helius RPC URL with API key"""
        if self.HELIUS_API_KEY:
            return f"https://devnet.helius-rpc.com/?api-key={self.HELIUS_API_KEY}"
        return self.SOLANA_RPC_URL
    
    # ============================================
    # Ethereum / Polygon Mumbai
    # ============================================
    ETHEREUM_RPC_URL: str = Field(default="https://rpc-mumbai.maticvigil.com", description="Polygon Mumbai RPC endpoint")
    ETHEREUM_CHAIN_ID: int = Field(default=80001, description="Polygon Mumbai Chain ID")
    ETHEREUM_CONTRACT_ADDRESS: Optional[str] = Field(default=None, description="NexusTrading contract address on Mumbai")
    ETHEREUM_EXPLORER: str = Field(default="https://mumbai.polygonscan.com", description="Polygon Mumbai Explorer URL")
    
    # Ethereum tokens on Mumbai
    ETHEREUM_WETH: str = Field(default="0x9c3C9283D3e44854697Cd22EDB54CB57F23A5A13")
    ETHEREUM_USDC: str = Field(default="0x0FA8781a83E46826621b3BC094Ea2A0212e71B23")
    ETHEREUM_USDT: str = Field(default="0xA02f6aDB06d98B855f8e0285c053EDA4cD51C89b")
    
    # Uniswap V3 on Mumbai
    ETHEREUM_UNISWAP_ROUTER: str = Field(default="0xE592427A0AEce92De3Edee1F18E0157C05861564")
    ETHEREUM_UNISWAP_QUOTER: str = Field(default="0xb27F1EF629B4CC20b86b40d41166FAACF0E5e5DF")
    
    # ============================================
    # Jupiter Aggregator
    # ============================================
    JUPITER_API_URL: str = Field(default="https://quote-api.jup.ag/v6")
    JUPITER_PRICE_API_URL: str = Field(default="https://price.jup.ag/v4")
    
    # ============================================
    # Birdeye API
    # ============================================
    BIRDEYE_API_KEY: Optional[str] = Field(default=None)
    BIRDEYE_API_URL: str = Field(default="https://public-api.birdeye.so")
    
    # Fallback
    COINGECKO_API_URL: str = Field(default="https://api.coingecko.com/api/v3")
    
    # ============================================
    # AI / LLM
    # ============================================
    # Anthropic (Claude)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022")
    ANTHROPIC_MAX_TOKENS: int = Field(default=4096)
    ANTHROPIC_TEMPERATURE: float = Field(default=0.7)
    
    # OpenAI (Fallback)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview")
    OPENAI_MAX_TOKENS: int = Field(default=4096)
    
    # LangSmith (Optional - for debugging)
    LANGCHAIN_TRACING_V2: bool = Field(default=False)
    LANGCHAIN_API_KEY: Optional[str] = Field(default=None)
    LANGCHAIN_PROJECT: str = Field(default="solana-copilot")
    
    # ============================================
    # Monitoring & Logging
    # ============================================
    # Sentry
    SENTRY_DSN: Optional[str] = Field(default=None)
    SENTRY_ENVIRONMENT: str = Field(default="development")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1)
    
    # Log Level
    LOG_LEVEL: str = Field(default="INFO")
    
    # ============================================
    # Notifications
    # ============================================
    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = Field(default=None)
    SENDGRID_FROM_EMAIL: str = Field(default="noreply@solanacopilot.com")
    
    # Slack
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None)
    
    # ============================================
    # Compliance
    # ============================================
    OFAC_SCREENING_ENABLED: bool = Field(default=False)
    OFAC_API_URL: Optional[str] = Field(default=None)
    
    KYC_ENABLED: bool = Field(default=False)
    KYC_PROVIDER: Optional[str] = Field(default=None)
    
    # ============================================
    # Feature Flags
    # ============================================
    FEATURE_DCA_ENABLED: bool = Field(default=True)
    FEATURE_REBALANCING_ENABLED: bool = Field(default=True)
    FEATURE_SESSION_KEYS_ENABLED: bool = Field(default=True)
    FEATURE_MULTISIG_ENABLED: bool = Field(default=False)
    FEATURE_VOICE_INPUT_ENABLED: bool = Field(default=False)
    
    # ============================================
    # Testing
    # ============================================
    TEST_DATABASE_URL: Optional[str] = Field(default=None)
    TEST_WALLET_ADDRESS: Optional[str] = Field(default=None)
    TEST_WALLET_PRIVATE_KEY: Optional[str] = Field(default=None)
    
    # ============================================
    # Validators
    # ============================================
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @field_validator("SOLANA_NETWORK")
    @classmethod
    def validate_solana_network(cls, v: str) -> str:
        """Validate Solana network is valid"""
        allowed = ["mainnet-beta", "devnet", "testnet", "localnet"]
        if v not in allowed:
            raise ValueError(f"SOLANA_NETWORK must be one of {allowed}")
        return v
    
    # ============================================
    # Computed Properties
    # ============================================
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL for SQLAlchemy"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


# ============================================
# Global Settings Instance
# ============================================
settings = Settings()
