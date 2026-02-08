"use client";

import React from "react";
import { NeoCard } from "@/components/ui/neo-card";
import { Button } from "@/components/ui/button";
import { PieChart as PieChartIcon, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Holding {
    mint: string;
    symbol: string;
    amount: number;
    price_usd: number;
    value_usd: number;
    allocation_pct: number;
}

export const CHART_COLORS = ["#8b5cf6", "#3b82f6", "#f97316", "#14b8a6", "#6366f1", "#ec4899", "#10b981"];

interface HoldingsTableProps {
    holdings: Holding[];
    loading?: boolean;
    onViewAll?: () => void;
}

export function formatCurrency(value: number) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
}

export function formatAmount(value: number) {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(2);
}

export function HoldingsTable({ holdings, loading = false, onViewAll }: HoldingsTableProps) {
    return (
        <NeoCard className="lg:col-span-2 p-6">
            <div className="flex items-center justify-between mb-6">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                    <PieChartIcon className="h-5 w-5 text-primary" />
                    Holdings
                </h3>
                <Button variant="ghost" size="sm" onClick={onViewAll}>View All</Button>
            </div>
            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : (
                <div className="space-y-1">
                    <div className="grid grid-cols-5 text-xs text-muted-foreground px-3 pb-2 border-b border-border">
                        <span>Asset</span>
                        <span>Amount</span>
                        <span className="text-right">Value</span>
                        <span className="text-right">Price</span>
                        <span className="text-right">Allocation</span>
                    </div>
                    {holdings.map((holding, index) => (
                        <div key={holding.mint} className="grid grid-cols-5 items-center py-3 px-3 hover:bg-muted/50 rounded-lg transition-colors">
                            <div className="flex items-center gap-3">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }} />
                                <div>
                                    <p className="font-medium text-foreground">{holding.symbol}</p>
                                </div>
                            </div>
                            <p className="text-sm text-foreground">{formatAmount(holding.amount)}</p>
                            <p className="text-sm text-foreground text-right">{formatCurrency(holding.value_usd)}</p>
                            <p className="text-sm text-muted-foreground text-right">{formatCurrency(holding.price_usd)}</p>
                            <p className="text-sm text-right text-muted-foreground">
                                {holding.allocation_pct.toFixed(1)}%
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </NeoCard>
    );
}
