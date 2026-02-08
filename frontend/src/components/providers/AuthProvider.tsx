"use client";

import React, { useEffect } from 'react';
import { useWallet } from '@solana/wallet-adapter-react';
import { useAuth } from '@/lib/hooks/useAuth';

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const { connected, publicKey } = useWallet();
    const { isAuthenticated, login } = useAuth();

    useEffect(() => {
        if (connected && publicKey && !isAuthenticated) {
            // Trigger login flow (sign message)
            // We verify if we already have a token first (handled inside useAuth)
            // If not, we prompt signature
            login();
        }
    }, [connected, publicKey, isAuthenticated, login]);

    return <>{children}</>;
}
