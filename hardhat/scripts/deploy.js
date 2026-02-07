/**
 * Hardhat Deployment Script for NexusTrading
 * Deploys to Polygon Mumbai Testnet
 * 
 * Usage:
 * npx hardhat run scripts/deploy.js --network mumbai
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
    console.log('🚀 Deploying NexusTrading to Polygon Mumbai...\n');
    
    // Get deployer account
    const [deployer] = await ethers.getSigners();
    console.log(`📝 Deploying with account: ${deployer.address}`);
    
    // Get account balance
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log(`💰 Account balance: ${ethers.formatEther(balance)} MATIC\n`);
    
    // Verify sufficient balance
    if (balance < ethers.parseEther('0.1')) {
        throw new Error('❌ Insufficient MATIC balance for deployment. Need at least 0.1 MATIC for Mumbai testnet.');
    }
    
    // ============================================
    // Deploy NexusTrading Contract
    // ============================================
    try {
        console.log('⏳ Compiling NexusTrading contract...');
        const NexusTrading = await ethers.getContractFactory('NexusTrading');
        
        console.log('📦 Deploying NexusTrading contract...');
        const nexusTrading = await NexusTrading.deploy();
        
        // Wait for deployment to complete
        await nexusTrading.waitForDeployment();
        
        console.log(`\n✅ NexusTrading deployed successfully!`);
        const contractAddress = await nexusTrading.getAddress();
        console.log(`📍 Contract Address: ${contractAddress}`);
        console.log(`🔗 Explorer: https://mumbai.polygonscan.com/address/${contractAddress}`);
        
        // ============================================
        // Save Deployment Information
        // ============================================
        const deploymentInfo = {
            network: 'mumbai',
            chainId: 80001,
            timestamp: new Date().toISOString(),
            deployer: deployer.address,
            contracts: {
                NexusTrading: {
                    address: contractAddress,
                },
            },
            rpc: 'https://polygon-mumbai.blockpi.network/v1/rpc/public',
            explorer: 'https://mumbai.polygonscan.com',
        };
        
        // Save to file in project root
        const deploymentPath = path.join(__dirname, '../deployments');
        if (!fs.existsSync(deploymentPath)) {
            fs.mkdirSync(deploymentPath, { recursive: true });
        }
        
        const filename = path.join(deploymentPath, `mumbai-${Date.now()}.json`);
        fs.writeFileSync(filename, JSON.stringify(deploymentInfo, null, 2));
        console.log(`\n💾 Deployment info saved to: ${filename}`);
        
        // Also save contract address to a simple text file for easy reference
        const addressFile = path.join(__dirname, '../contract_address.txt');
        fs.writeFileSync(addressFile, `NexusTrading=${contractAddress}\n`);
        fs.appendFileSync(addressFile, `Network=mumbai\n`);
        fs.appendFileSync(addressFile, `ChainID=80001\n`);
        console.log(`📄 Contract address saved to: ${addressFile}`);
        
        // ============================================
        // Test Contract Functions (Optional)
        // ============================================
        console.log('\n🧪 Testing contract functions...');
        try {
            const balance = await nexusTrading.getBalance(deployer.address);
            console.log(`✅ getBalance() works: ${balance}`);
        } catch (error) {
            console.log('⚠️ Test call failed (contract might not be fully deployed yet)');
        }
        
        // ============================================
        // Summary
        // ============================================
        console.log('\n' + '='.repeat(60));
        console.log('🎉 DEPLOYMENT SUCCESSFUL!');
        console.log('='.repeat(60));
        console.log(`
Contract Details:
  Name:      NexusTrading
  Address:   ${contractAddress}
  Network:   Polygon Mumbai Testnet
  Chain ID:  80001
  
Network Details:
  RPC:       https://polygon-mumbai.blockpi.network/v1/rpc/public
  Explorer:  https://mumbai.polygonscan.com
  
Next Steps:
  1. Update backend/app/core/config.py with the contract address
  2. Set ETHEREUM_CONTRACT_ADDRESS=${contractAddress}
  3. Test swap functions via the backend API
  4. Deploy to production when ready

Useful Links:
  🔗 View Contract: https://mumbai.polygonscan.com/address/${contractAddress}
  🔗 Get Test MATIC: https://faucet.polygon.technology/
  🔗 Bridge Tokens: https://bridge.polygon.technology/
`);
        
        return contractAddress;
        
    } catch (error) {
        console.error('\n❌ Deployment failed!');
        console.error('Error:', error.message);
        
        if (error.message.includes('insufficient funds')) {
            console.error('\n💡 Solution: Get test MATIC from https://faucet.polygon.technology/');
        }
        
        throw error;
    }
}

main()
    .then((address) => {
        console.log(`\n✨ Deployment complete. Contract: ${address}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
