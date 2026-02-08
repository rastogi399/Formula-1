"use client";

import React from "react";
import { NeoCard } from "@/components/ui/neo-card";
import { ArrowUpRight, ArrowDownRight, TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency, Holding } from "./HoldingsTable";

interface Performance {
    total_pnl_usd: number;
    total_pnl_pct: number;
    return_1d_pct: number;
    return_7d_pct: number;
    return_30d_pct: number;
}

interface PerformanceStatsProps {
    totalValue: number;
    performance: Performance;
    holdings: Holding[];
    loading?: boolean;
}

export function PerformanceStats({ totalValue, performance, holdings, loading = false }: PerformanceStatsProps) {
    const sortedByAllocation = [...holdings].sort((a, b) => b.allocation_pct - a.allocation_pct);
    const bestPerformer = sortedByAllocation[0];
    const worstPerformer = sortedByAllocation[sortedByAllocation.length - 1];

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <NeoCard className="p-5">
                <p className="text-sm text-muted-foreground">Total Value</p>
                {loading ? (
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mt-2" />
                ) : (
                    <>
                        <h3 className="text-2xl font-bold text-foreground mt-1">{formatCurrency(totalValue)}</h3>
                        <div className={cn(
                            "flex items-center gap-1 mt-2 text-xs font-medium",
                            performance.total_pnl_pct >= 0 ? "text-emerald-500" : "text-red-500"
                        )}>
                            {performance.total_pnl_pct >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                            <span>{performance.total_pnl_pct >= 0 ? '+' : ''}{formatCurrency(performance.total_pnl_usd)} ({performance.total_pnl_pct.toFixed(1)}%)</span>
                        </div>
                    </>
                )}
            </NeoCard>
            <NeoCard className="p-5">
                <p className="text-sm text-muted-foreground">24h Change</p>
                {loading ? (
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mt-2" />
                ) : (
                    <>
                        <h3 className={cn(
                            "text-2xl font-bold mt-1",
                            performance.return_1d_pct >= 0 ? "text-emerald-500" : "text-red-500"
                        )}>
                            {performance.return_1d_pct >= 0 ? '+' : ''}{performance.return_1d_pct.toFixed(1)}%
                        </h3>
                        <p className="text-xs text-muted-foreground mt-2">from yesterday</p>
                    </>
                )}
            </NeoCard>
            <NeoCard className="p-5">
                <p className="text-sm text-muted-foreground">Largest Holding</p>
                <h3 className="text-2xl font-bold text-foreground mt-1">{bestPerformer?.symbol || '...'}</h3>
                <div className="flex items-center gap-1 mt-2 text-emerald-500 text-xs font-medium">
                    <TrendingUp className="h-3 w-3" />
                    <span>{bestPerformer?.allocation_pct?.toFixed(1) || 0}% of portfolio</span>
                </div>
            </NeoCard>
            <NeoCard className="p-5">
                <p className="text-sm text-muted-foreground">Smallest Holding</p>
                <h3 className="text-2xl font-bold text-foreground mt-1">{worstPerformer?.symbol || '...'}</h3>
                <div className="flex items-center gap-1 mt-2 text-muted-foreground text-xs font-medium">
                    <TrendingDown className="h-3 w-3" />
                    <span>{worstPerformer?.allocation_pct?.toFixed(1) || 0}% of portfolio</span>
                </div>
            </NeoCard>
        </div>
    );
}
