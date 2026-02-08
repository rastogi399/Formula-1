"use client";
import React, { useEffect, useState } from "react";
import { NeoCard } from "@/components/ui/neo-card";
import { Button } from "@/components/ui/button";
import { Wallet, BarChart3, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { portfolioApi, transactionsApi } from "@/lib/api";
import {
    HoldingsTable,
    AllocationChart,
    PerformanceStats,
    PortfolioChart,
    Holding as BaseHolding,
    formatAmount as baseFormatAmount
} from "@/components/portfolio";

// Use local formatters if needed or alias imported ones
const formatAmount = baseFormatAmount;
// Use local helper for time ago which wasn't extracted
const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return 'just now';
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
};

// Aliasing type to match local usage
type Holding = BaseHolding;

// Types
interface Transaction {
    id: string;
    action: string;
    source_token: string;
    dest_token: string;
    amount_in: number;
    amount_out: number;
    status: string;
    created_at: string;
}

interface Performance {
    total_pnl_usd: number;
    total_pnl_pct: number;
    return_1d_pct: number;
    return_7d_pct: number;
    return_30d_pct: number;
}

export default function PortfolioPage() {
    const [holdings, setHoldings] = useState<Holding[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [performance, setPerformance] = useState<Performance | null>(null);
    const [totalValue, setTotalValue] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            setError(null);

            try {
                const [portfolioRes, transactionsRes, performanceRes] = await Promise.allSettled([
                    portfolioApi.getHoldings(),
                    transactionsApi.getTransactions(10),
                    portfolioApi.getPerformance('30d'),
                ]);

                if (portfolioRes.status === 'fulfilled') {
                    const h = portfolioRes.value || [];
                    setHoldings(h);
                    setTotalValue(h.reduce((acc: number, item: Holding) => acc + item.value_usd, 0));
                }

                if (transactionsRes.status === 'fulfilled') {
                    setTransactions(transactionsRes.value?.transactions || []);
                }

                if (performanceRes.status === 'fulfilled') {
                    setPerformance(performanceRes.value);
                }

            } catch (err) {
                console.error('Portfolio fetch error:', err);
                setError('Failed to load portfolio data.');
            } finally {
                setLoading(false);
            }
        }

        fetchData();
    }, []);

    // Fallback data
    const displayHoldings = holdings.length > 0 ? holdings : [
        { mint: "SOL", symbol: "SOL", amount: 145.2, price_usd: 72, value_usd: 10450, allocation_pct: 66.4 },
        { mint: "USDC", symbol: "USDC", amount: 4500, price_usd: 1, value_usd: 4500, allocation_pct: 28.6 },
        { mint: "BONK", symbol: "BONK", amount: 15000000, price_usd: 0.00001893, value_usd: 284, allocation_pct: 1.8 },
        { mint: "RAY", symbol: "RAY", amount: 120, price_usd: 1.5, value_usd: 180, allocation_pct: 1.1 },
        { mint: "JUP", symbol: "JUP", amount: 500, price_usd: 0.64, value_usd: 320, allocation_pct: 2.0 },
    ];

    const displayTotal = totalValue > 0 ? totalValue : displayHoldings.reduce((acc, h) => acc + h.value_usd, 0);
    const displayPerformance = performance || { total_pnl_usd: 1234, total_pnl_pct: 8.5, return_1d_pct: 2.1, return_7d_pct: 5.3, return_30d_pct: 12.0 };
    const displayTransactions = transactions.length > 0 ? transactions : [];


    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Portfolio</h1>
                    <p className="text-muted-foreground">Track your holdings and performance</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline">
                        <BarChart3 className="h-4 w-4 mr-2" />
                        Export
                    </Button>
                    <Button className="bg-primary hover:bg-primary/90 text-primary-foreground">
                        <Wallet className="h-4 w-4 mr-2" />
                        Add Wallet
                    </Button>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="p-3 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-lg">
                    <p className="text-sm text-amber-700 dark:text-amber-400">{error}</p>
                </div>
            )}

            {/* Stats Grid */}
            <PerformanceStats
                totalValue={displayTotal}
                performance={displayPerformance}
                holdings={displayHoldings}
                loading={loading}
            />

            {/* Portfolio Chart */}
            <PortfolioChart />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Holdings Table */}
                <HoldingsTable
                    holdings={displayHoldings}
                    loading={loading}
                />

                {/* Allocation Chart */}
                <AllocationChart
                    holdings={displayHoldings}
                />
            </div>

            {/* Transaction History */}
            <NeoCard className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="font-semibold text-foreground">Recent Transactions</h3>
                    <Button variant="ghost" size="sm">View All</Button>
                </div>
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : displayTransactions.length > 0 ? (
                    <div className="space-y-1">
                        <div className="grid grid-cols-5 text-xs text-muted-foreground px-3 pb-2 border-b border-border">
                            <span>Type</span>
                            <span>Asset</span>
                            <span>Amount</span>
                            <span>Time</span>
                            <span className="text-right">Status</span>
                        </div>
                        {displayTransactions.map((tx) => (
                            <div key={tx.id} className="grid grid-cols-5 items-center py-3 px-3 hover:bg-muted/50 rounded-lg transition-colors">
                                <span className={cn(
                                    "text-xs font-medium px-2 py-1 rounded-full w-fit capitalize",
                                    tx.action === "swap" ? "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400" :
                                        tx.action === "send" ? "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400" :
                                            tx.action === "stake" ? "bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400" :
                                                "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400"
                                )}>
                                    {tx.action}
                                </span>
                                <span className="text-sm text-foreground">{tx.source_token} → {tx.dest_token}</span>
                                <span className="text-sm text-foreground">{formatAmount(tx.amount_in)}</span>
                                <span className="text-sm text-muted-foreground">{formatTimeAgo(tx.created_at)}</span>
                                <span className={cn(
                                    "text-xs text-right capitalize",
                                    tx.status === "success" ? "text-emerald-500" : tx.status === "pending" ? "text-amber-500" : "text-red-500"
                                )}>
                                    {tx.status}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-muted-foreground">
                        <p>No transactions yet</p>
                    </div>
                )}
            </NeoCard>
        </div>
    );
}
