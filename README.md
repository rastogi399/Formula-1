
🤖 Schmatcher - Autonomous AI DeFi Agent

Smart contract-powered DeFi automation with conversational AI
An intelligent agent that autonomously manages, analyzes, and optimizes blockchain transactions across multiple chains.

✅ Smart contracts on Ethereum/EVM chains (Polygon Mumbai)

✅ Trade automation & DeFi: Token swaps, portfolio tracking, DCA, recurring swaps

✅ Integration with Web3.py, Uniswap V3, Solana programs

✅ Full-stack: UI + API + Smart Contracts + AI Agent

✅ Production-ready deployed smart contracts

🚀 Revolution: Users can trade, rebalance, and automate portfolio strategies across multiple blockchains using natural language — this is a new level of non-custodial autonomous trading.

📋 Overview

Schmatcher allows users to:

Converse naturally in English about crypto transactions

Automatically execute token swaps, transfers, and portfolio operations

Cross-chain support: Ethereum/Polygon + Solana

Non-custodial: Users retain control of wallets

Real-time portfolio tracking and gas-optimized transactions

Example Interactions
User: "Swap 1 WETH for USDC"
→ Agent executes best route → Returns confirmation

User: "What's my portfolio worth?"
→ Fetch balances → Calculate USD value → Show breakdown

User: "Set up a DCA strategy for Bitcoin"
→ Create recurring swap → Execute daily

✨ Features
🤖 AI-Powered Chat Interface

Natural Language Commands: "Swap 10 SOL to USDC", "Show portfolio", "Set up weekly DCA"

Intent Classification with LangGraph & LangChain

Transaction Simulation: Preview outputs before signing

Multi-Chain Support: Ethereum primary, Solana backup

💼 Portfolio Management

Real-time holdings & USD value across tokens

Risk analysis: Volatility, drawdown, Value-at-Risk

Performance tracking (PnL, 24h/7d/30d changes)

Cross-chain portfolio view

🔄 DCA & Automation

Dollar-Cost Averaging

Recurring swaps & portfolio rebalancing

Multi-chain execution

🔐 Security

Non-custodial & sign-only authentication

Session keys for Solana

Smart contract protections: ReentrancyGuard, simulation, event logging

🏗️ Architecture
Frontend (Next.js) → FastAPI API → AI Agent → Blockchain Services → Smart Contracts (Ethereum & Solana)


Frontend: Next.js 15, React, TypeScript, Tailwind

Backend: FastAPI, Python 3.12, SQLAlchemy, Celery

AI/LLM: LangChain, Anthropic Claude, OpenAI

Blockchain: Web3.py, Ethers.js, Hardhat, Solana programs

Database: PostgreSQL, Redis

📁 Project Structure
Schmatcher/
├── frontend/                  # Next.js UI
├── backend/                   # FastAPI backend
├── hardhat/                   # Ethereum smart contracts
├── programs/                  # Solana programs
│   ├── dca-vault/
│   └── session-keys/
├── docker-compose.yml
├── package.json
├── package-lock.json
├── Anchor.toml
└── README.md

🔌 API Endpoints
Portfolio
GET /api/v1/portfolio/{wallet_address}
GET /api/v1/balance/{token}/{wallet_address}

Transactions
POST /api/v1/transactions/swap
POST /api/v1/transactions/simulate
GET /api/v1/transactions/{tx_hash}

AI Chat
POST /api/v1/chat
WebSocket: ws://localhost:8000/ws/chat/{user_id}

Blockchain Info
GET /api/v1/chain-info
GET /api/v1/tokens

🚀 Quick Start
1️⃣ Clone & Install
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
cd ../hardhat && npm install

2️⃣ Environment Setup
cp .env.example .env
# Fill API keys, Ethereum & Solana config, database URLs

3️⃣ Start Services
# Backend
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
npm run dev --prefix frontend

# Celery workers
celery -A backend.app.workers.celery_app worker --loglevel=info

📝 Documentation

START_HERE.md - First steps

ETHEREUM_DEPLOYMENT.md - Ethereum guide

ETHEREUM_QUICK_REFERENCE.md - Quick commands

ARCHITECTURE.md - System design & workflow

🆘 Troubleshooting

Contract deployment fails → Get test MATIC

Web3 timeout → Check RPC URLs

Wrong chain in frontend → Clear browser cache, verify ACTIVE_CHAIN in .env
