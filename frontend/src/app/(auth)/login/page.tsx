"use client";

import { useEffect } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useRouter } from "next/navigation";
import { Bot, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/hooks/useAuth";

export default function LoginPage() {
    const { connected } = useWallet();
    const { login, isLoading, isAuthenticated } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (isAuthenticated) {
            router.push("/dashboard");
        }
    }, [isAuthenticated, router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-black relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/20 rounded-full blur-[120px] opacity-30" />
            </div>

            <div className="relative z-10 w-full max-w-md p-8">
                <div className="flex flex-col items-center text-center space-y-8">
                    {/* Logo */}
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-2xl shadow-primary/20">
                        <Bot className="w-8 h-8 text-white" />
                    </div>

                    <div className="space-y-2">
                        <h1 className="text-3xl font-bold text-white">Welcome Back</h1>
                        <p className="text-muted-foreground">
                            Connect your wallet to access your intelligent companion
                        </p>
                    </div>

                    <div className="w-full space-y-4 p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
                        <div className="flex justify-center">
                            <WalletMultiButton className="!bg-primary hover:!bg-primary/90 !h-12 !w-full !justify-center !rounded-lg" />
                        </div>

                        {connected && (
                            <Button
                                className="w-full h-12 text-lg"
                                onClick={login}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                        Signing In...
                                    </>
                                ) : (
                                    "Sign In with Wallet"
                                )}
                            </Button>
                        )}

                        {!connected && (
                            <p className="text-xs text-center text-muted-foreground mt-4">
                                Select your Solana wallet to continue
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
