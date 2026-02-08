"use client";

import React from "react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { DashboardThemeToggle } from "@/components/ui/dashboard-theme-toggle";

export function DashboardHeader() {
    return (
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/80 px-6 backdrop-blur-md">
            <div className="flex-1" />
            <div className="flex items-center gap-4">
                <WalletMultiButton className="!bg-primary hover:!bg-primary/90 !rounded-lg !h-10 !font-sans !font-bold !px-4" />
                <DashboardThemeToggle />
            </div>
        </header>
    );
}

