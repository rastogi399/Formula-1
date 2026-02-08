/**
 * Application-wide constants
 * Extracted to avoid magic numbers and enable easy configuration
 */

// Risk Analysis Thresholds
export const RISK_THRESHOLDS = {
    CONCENTRATION_WARNING: 80, // Percentage
    VOLATILITY_WARNING: 10,    // Percentage
    DRAWDOWN_WARNING: 20,      // Percentage
    HEALTHY_RISK_SCORE: 30,    // 0-100 score
} as const;

// Automation Frequencies (in seconds)
export const AUTOMATION_FREQUENCIES = {
    HOURLY: 3600,
    DAILY: 86400,
    WEEKLY: 604800,
    MONTHLY: 2592000,
} as const;

// Token Decimals
export const TOKEN_DECIMALS = {
    SOL: 9,
    USDC: 6,
    USDT: 6,
    DEFAULT: 6,
} as const;

// API Pagination Defaults
export const PAGINATION = {
    DEFAULT_LIMIT: 50,
    MAX_LIMIT: 100,
    DEFAULT_OFFSET: 0,
} as const;

// UI Constants
export const UI = {
    MODAL_ANIMATION_MS: 200,
    TOAST_DURATION_MS: 5000,
    DEBOUNCE_MS: 300,
} as const;

// Risk Levels
export const RISK_LEVELS = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical',
} as const;

// Automation Types
export const AUTOMATION_TYPES = {
    DCA: 'dca',
    STOP_LOSS: 'stop_loss',
    TAKE_PROFIT: 'take_profit',
    REBALANCE: 'rebalance',
} as const;

// Automation Status
export const AUTOMATION_STATUS = {
    ACTIVE: 'active',
    PAUSED: 'paused',
    PENDING_DEPLOYMENT: 'pending_deployment',
    COMPLETED: 'completed',
    CANCELLED: 'cancelled',
} as const;
