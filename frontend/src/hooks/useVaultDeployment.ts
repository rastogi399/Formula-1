"use client";

import { useConnection, useWallet } from "@solana/wallet-adapter-react";
import {
    Connection,
    PublicKey,
    Transaction,
    TransactionInstruction,
    SystemProgram,
    LAMPORTS_PER_SOL,
} from "@solana/web3.js";
import { useState, useCallback } from "react";

/** DCA Vault Program ID */
const DCA_VAULT_PROGRAM_ID = new PublicKey("DCAvau1tXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX");

/** Common token mints */
export const TOKEN_MINTS = {
    SOL: new PublicKey("So11111111111111111111111111111111111111112"),
    USDC: new PublicKey("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
    USDT: new PublicKey("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"),
} as const;

interface VaultDeploymentResult {
    success: boolean;
    signature?: string;
    vaultPda?: string;
    error?: string;
}

interface DeployVaultParams {
    sourceMint: string;
    destMint: string;
    amountPerCycle: number;
    frequencySeconds: number;
    totalCycles: number;
}

/**
 * Derive the vault PDA address
 */
function deriveVaultPda(
    owner: PublicKey,
    sourceMint: PublicKey,
    destMint: PublicKey
): [PublicKey, number] {
    return PublicKey.findProgramAddressSync(
        [
            Buffer.from("vault"),
            owner.toBuffer(),
            sourceMint.toBuffer(),
            destMint.toBuffer(),
        ],
        DCA_VAULT_PROGRAM_ID
    );
}

/**
 * Resolve token symbol to mint address
 */
function resolveMint(token: string): PublicKey {
    const upperToken = token.toUpperCase();
    if (upperToken in TOKEN_MINTS) {
        return TOKEN_MINTS[upperToken as keyof typeof TOKEN_MINTS];
    }
    return new PublicKey(token);
}

/**
 * Hook for deploying DCA vaults on-chain
 * Handles transaction building, signing, and submission
 */
export function useVaultDeployment() {
    const { connection } = useConnection();
    const { publicKey, signTransaction, sendTransaction } = useWallet();

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    /**
     * Deploy a new DCA vault on-chain
     */
    const deployVault = useCallback(async (
        params: DeployVaultParams
    ): Promise<VaultDeploymentResult> => {
        if (!publicKey || !signTransaction) {
            return { success: false, error: "Wallet not connected" };
        }

        setLoading(true);
        setError(null);

        try {
            const sourceMint = resolveMint(params.sourceMint);
            const destMint = resolveMint(params.destMint);

            // Derive vault PDA
            const [vaultPda, bump] = deriveVaultPda(publicKey, sourceMint, destMint);

            // Build the initialize_vault instruction data
            // Format: [instruction_discriminator (8 bytes), amount_per_cycle (8), frequency_seconds (8), total_cycles (2)]
            const discriminator = Buffer.from([
                0x47, 0x5b, 0xc9, 0x4a, 0x1a, 0x1b, 0x6d, 0xe3, // initialize_vault discriminator
            ]);

            const data = Buffer.alloc(26);
            discriminator.copy(data, 0);
            data.writeBigUInt64LE(BigInt(params.amountPerCycle), 8);
            data.writeBigInt64LE(BigInt(params.frequencySeconds), 16);
            data.writeUInt16LE(params.totalCycles, 24);

            // Build instruction
            const instruction = new TransactionInstruction({
                keys: [
                    { pubkey: vaultPda, isSigner: false, isWritable: true },
                    { pubkey: publicKey, isSigner: true, isWritable: true },
                    { pubkey: sourceMint, isSigner: false, isWritable: false },
                    { pubkey: destMint, isSigner: false, isWritable: false },
                    { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
                ],
                programId: DCA_VAULT_PROGRAM_ID,
                data,
            });

            // Build transaction
            const transaction = new Transaction().add(instruction);
            transaction.feePayer = publicKey;
            transaction.recentBlockhash = (
                await connection.getLatestBlockhash()
            ).blockhash;

            // Sign and send
            const signature = await sendTransaction(transaction, connection);

            // Wait for confirmation
            const confirmation = await connection.confirmTransaction(signature, "confirmed");

            if (confirmation.value.err) {
                throw new Error(`Transaction failed: ${confirmation.value.err}`);
            }

            console.log("Vault deployed successfully:", signature);

            return {
                success: true,
                signature,
                vaultPda: vaultPda.toBase58(),
            };

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to deploy vault";
            console.error("Vault deployment error:", err);
            setError(errorMessage);
            return { success: false, error: errorMessage };
        } finally {
            setLoading(false);
        }
    }, [publicKey, signTransaction, sendTransaction, connection]);

    /**
     * Pause an existing vault
     */
    const pauseVault = useCallback(async (
        vaultPda: string
    ): Promise<VaultDeploymentResult> => {
        if (!publicKey || !signTransaction) {
            return { success: false, error: "Wallet not connected" };
        }

        setLoading(true);
        setError(null);

        try {
            const vaultPubkey = new PublicKey(vaultPda);

            // pause_vault discriminator
            const discriminator = Buffer.from([
                0x5f, 0x4b, 0x6a, 0x1c, 0x2d, 0x3e, 0x4f, 0x50,
            ]);

            const instruction = new TransactionInstruction({
                keys: [
                    { pubkey: vaultPubkey, isSigner: false, isWritable: true },
                    { pubkey: publicKey, isSigner: true, isWritable: false },
                ],
                programId: DCA_VAULT_PROGRAM_ID,
                data: discriminator,
            });

            const transaction = new Transaction().add(instruction);
            transaction.feePayer = publicKey;
            transaction.recentBlockhash = (
                await connection.getLatestBlockhash()
            ).blockhash;

            const signature = await sendTransaction(transaction, connection);
            await connection.confirmTransaction(signature, "confirmed");

            return { success: true, signature };

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to pause vault";
            setError(errorMessage);
            return { success: false, error: errorMessage };
        } finally {
            setLoading(false);
        }
    }, [publicKey, signTransaction, sendTransaction, connection]);

    /**
     * Resume a paused vault
     */
    const resumeVault = useCallback(async (
        vaultPda: string
    ): Promise<VaultDeploymentResult> => {
        if (!publicKey || !signTransaction) {
            return { success: false, error: "Wallet not connected" };
        }

        setLoading(true);
        setError(null);

        try {
            const vaultPubkey = new PublicKey(vaultPda);

            // resume_vault discriminator
            const discriminator = Buffer.from([
                0x6a, 0x5b, 0x7c, 0x2d, 0x3e, 0x4f, 0x50, 0x61,
            ]);

            const instruction = new TransactionInstruction({
                keys: [
                    { pubkey: vaultPubkey, isSigner: false, isWritable: true },
                    { pubkey: publicKey, isSigner: true, isWritable: false },
                ],
                programId: DCA_VAULT_PROGRAM_ID,
                data: discriminator,
            });

            const transaction = new Transaction().add(instruction);
            transaction.feePayer = publicKey;
            transaction.recentBlockhash = (
                await connection.getLatestBlockhash()
            ).blockhash;

            const signature = await sendTransaction(transaction, connection);
            await connection.confirmTransaction(signature, "confirmed");

            return { success: true, signature };

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to resume vault";
            setError(errorMessage);
            return { success: false, error: errorMessage };
        } finally {
            setLoading(false);
        }
    }, [publicKey, signTransaction, sendTransaction, connection]);

    return {
        deployVault,
        pauseVault,
        resumeVault,
        loading,
        error,
        isConnected: !!publicKey,
    };
}
