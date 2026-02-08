import { useWallet } from "@solana/wallet-adapter-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";
import bs58 from "bs58";
import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/store/authStore";
import { useRouter } from "next/navigation";

export function useAuth() {
    const { publicKey, signMessage, disconnect } = useWallet();
    const { setAuth, clearAuth, isAuthenticated, user } = useAuthStore();
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const login = useCallback(async () => {
        if (!publicKey || !signMessage) {
            toast.error("Wallet not connected");
            return;
        }

        try {
            setIsLoading(true);
            const walletAddress = publicKey.toBase58();

            // 1. Request Challenge
            const { message, nonce } = await authApi.requestChallenge(walletAddress);

            // 2. Sign Message
            const encodedMessage = new TextEncoder().encode(message);
            const signatureBytes = await signMessage(encodedMessage);
            const signature = bs58.encode(signatureBytes);

            // 3. Verify Signature
            const response = await authApi.verifySignature(
                walletAddress,
                message,
                signature
            );

            // 4. Get User Details (optional, or use response data)
            // For now, we'll construct a basic user object if not returned fully
            const user = {
                id: "temp-id", // In real app, get from response or /me endpoint
                wallet_address: walletAddress,
                created_at: new Date().toISOString(),
            };

            // 5. Update Store
            setAuth(response.token, user);
            toast.success("Logged in successfully");
            router.push("/dashboard");

        } catch (error: any) {
            console.error("Login error:", error);
            toast.error(error.response?.data?.detail || "Failed to login");
            disconnect();
        } finally {
            setIsLoading(false);
        }
    }, [publicKey, signMessage, setAuth, router, disconnect]);

    const logout = useCallback(async () => {
        try {
            await authApi.logout();
        } catch (error) {
            // Ignore logout errors
        } finally {
            clearAuth();
            disconnect();
            router.push("/");
            toast.success("Logged out");
        }
    }, [clearAuth, disconnect, router]);

    return {
        login,
        logout,
        isLoading,
        isAuthenticated,
        user,
    };
}
