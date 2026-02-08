import type { Metadata } from "next";
import { Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import "@solana/wallet-adapter-react-ui/styles.css";
import { SolanaWalletProvider } from "@/components/providers/WalletProvider";

import QueryProvider from "@/components/providers/QueryProvider";
import { AuthProvider } from "@/components/providers/AuthProvider";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const ibmPlexMono = IBM_Plex_Mono({
    weight: ["400", "500", "600"],
    subsets: ["latin"],
    variable: "--font-mono",
});

export const metadata: Metadata = {
    title: "Schumacher - AI Agent Wallet",
    description: "Your intelligent companion for Solana DeFi",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={`${inter.variable} ${ibmPlexMono.variable} font-sans antialiased bg-background text-foreground`}>
                <QueryProvider>
                    <SolanaWalletProvider>
                        <AuthProvider>
                            {children}
                            <Toaster position="top-right" richColors />
                        </AuthProvider>
                    </SolanaWalletProvider>
                </QueryProvider>

            </body>
        </html>
    );
}
