#!/bin/bash

# Solana Anchor dca-vault Safe Deploy Script (fixed for "String is the wrong size")
set -e

echo "================================"
echo "DCA-Vault Safe Deploy Script"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_ROOT=$(pwd)
PROGRAM_KEYPAIR="$PROJECT_ROOT/target/deploy/dca_vault-keypair.json"

# Step 1: Clean build artifacts only
echo -e "${YELLOW}[1/5]${NC} Cleaning old build artifacts..."
rm -rf "$PROJECT_ROOT/target/"
echo -e "${GREEN}✓${NC} target/ folder deleted"

# Step 1b: Remove old Anchor program metadata (this fixes "String is wrong size")
if [ -d "$PROJECT_ROOT/.anchor/programs" ]; then
    rm -rf "$PROJECT_ROOT/.anchor/programs/"
    echo -e "${GREEN}✓${NC} Removed old .anchor/programs metadata"
fi

# Step 2: Check program keypair
echo -e "${YELLOW}[2/5]${NC} Checking program keypair..."
if [ ! -f "$PROGRAM_KEYPAIR" ]; then
    echo "Program keypair not found. Generating new one..."
    mkdir -p "$PROJECT_ROOT/target/deploy"
    solana-keygen new --force --silent --outfile "$PROGRAM_KEYPAIR"
    NEW_PROGRAM_ID=$(solana address -k "$PROGRAM_KEYPAIR")
    echo -e "${YELLOW}⚠ New Program ID: $NEW_PROGRAM_ID${NC}"
    echo "   Update src/lib.rs declare_id! and Anchor.toml [programs.devnet]"
else
    CURRENT_PROGRAM_ID=$(solana address -k "$PROGRAM_KEYPAIR")
    echo -e "${GREEN}✓${NC} Using existing program keypair: $CURRENT_PROGRAM_ID"
fi

# Step 3: Build program
echo -e "${YELLOW}[3/5]${NC} Building program..."
anchor build --provider.cluster devnet
echo -e "${GREEN}✓${NC} Build completed"

# Step 4: Verify binary
if [ -f "$PROJECT_ROOT/target/debug/dca_vault.so" ]; then
    BINARY_SIZE=$(stat -f%z "_
