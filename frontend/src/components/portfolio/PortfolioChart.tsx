"use client";
import React, { useEffect, useState } from "react";
import { NeoCard } from "@/components/ui/neo-card";
import { Button } from "@/components/ui/button";
import { TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { portfolioApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface HistoryDataPoint {
    timestamp: string;
    value_usd: number;
    risk_score: number | null;
}

interface HistorySummary {
    start_value: number;
    end_value: number;
    change_usd: number;
    change_pct: number;
    high: number;
    low: number;
}

interface PortfolioHistoryResponse {
    timeframe: string;
    data_points: number;
    history: HistoryDataPoint[];
    summary: HistorySummary;
}

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(value);
};

export function PortfolioChart() {
    const [timeframe, setTimeframe] = useState<string>("30d");
    const [data, setData] = useState<PortfolioHistoryResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchHistory() {
            setLoading(true);
            setError(null);

            try {
                const response = await portfolioApi.getHistory(timeframe);
                setData(response);
            } catch (err) {
                console.error('Portfolio history fetch error:', err);
                setError('Failed to load portfolio history');
            } finally {
                setLoading(false);
            }
        }

        fetchHistory();
    }, [timeframe]);

    const timeframes = [
        { label: "7D", value: "7d" },
        { label: "30D", value: "30d" },
        { label: "90D", value: "90d" },
        { label: "1Y", value: "1y" },
    ];

    // Calculate chart dimensions
    const chartWidth = 100;
    const chartHeight = 60;
    const paddingTop = 5;
    const paddingBottom = 5;

    // Generate SVG path for the chart
    const generatePath = () => {
        if (!data || data.history.length < 2) return "";

        const values = data.history.map(d => d.value_usd);
        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const range = maxValue - minValue || 1;

        const points = data.history.map((point, index) => {
            const x = (index / (data.history.length - 1)) * chartWidth;
            const y = paddingTop + ((maxValue - point.value_usd) / range) * (chartHeight - paddingTop - paddingBottom);
            return `${x},${y}`;
        });

        return `M ${points.join(" L ")}`;
    };

    // Generate area fill path
    const generateAreaPath = () => {
        if (!data || data.history.length < 2) return "";

        const values = data.history.map(d => d.value_usd);
        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const range = maxValue - minValue || 1;

        const points = data.history.map((point, index) => {
            const x = (index / (data.history.length - 1)) * chartWidth;
            const y = paddingTop + ((maxValue - point.value_usd) / range) * (chartHeight - paddingTop - paddingBottom);
            return `${x},${y}`;
        });

        return `M 0,${chartHeight} L ${points.join(" L ")} L ${chartWidth},${chartHeight} Z`;
    };

    const isPositive = data ? data.summary.change_pct >= 0 : true;

    return (
        <NeoCard className="p-6">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="font-semibold text-foreground">Portfolio Value</h3>
                    <p className="text-sm text-muted-foreground">Historical performance</p>
                </div>
                <div className="flex gap-1 bg-muted/50 rounded-lg p-1">
                    {timeframes.map((tf) => (
                        <Button
                            key={tf.value}
                            variant={timeframe === tf.value ? "default" : "ghost"}
                            size="sm"
                            className={cn(
                                "px-3 h-7 text-xs",
                                timeframe === tf.value && "bg-primary text-primary-foreground"
                            )}
                            onClick={() => setTimeframe(tf.value)}
                        >
                            {tf.label}
                        </Button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-16">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : error ? (
                <div className="text-center py-16 text-muted-foreground">
                    <p>{error}</p>
                </div>
            ) : data && data.history.length > 0 ? (
                <>
                    {/* Value display */}
                    <div className="flex items-baseline gap-4 mb-6">
                        <span className="text-3xl font-bold text-foreground">
                            {formatCurrency(data.summary.end_value)}
                        </span>
                        <div className={cn(
                            "flex items-center gap-1 text-sm font-medium",
                            isPositive ? "text-emerald-500" : "text-red-500"
                        )}>
                            {isPositive ? (
                                <TrendingUp className="h-4 w-4" />
                            ) : (
                                <TrendingDown className="h-4 w-4" />
                            )}
                            <span>
                                {isPositive ? "+" : ""}{data.summary.change_pct.toFixed(2)}%
                            </span>
                            <span className="text-muted-foreground">
                                ({isPositive ? "+" : ""}{formatCurrency(data.summary.change_usd)})
                            </span>
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="relative h-40 w-full">
                        <svg
                            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                            preserveAspectRatio="none"
                            className="w-full h-full"
                        >
                            {/* Gradient definition */}
                            <defs>
                                <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                    <stop
                                        offset="0%"
                                        stopColor={isPositive ? "rgb(16, 185, 129)" : "rgb(239, 68, 68)"}
                                        stopOpacity="0.3"
                                    />
                                    <stop
                                        offset="100%"
                                        stopColor={isPositive ? "rgb(16, 185, 129)" : "rgb(239, 68, 68)"}
                                        stopOpacity="0"
                                    />
                                </linearGradient>
                            </defs>

                            {/* Area fill */}
                            <path
                                d={generateAreaPath()}
                                fill="url(#chartGradient)"
                            />

                            {/* Line */}
                            <path
                                d={generatePath()}
                                fill="none"
                                stroke={isPositive ? "rgb(16, 185, 129)" : "rgb(239, 68, 68)"}
                                strokeWidth="0.5"
                                vectorEffect="non-scaling-stroke"
                            />
                        </svg>
                    </div>

                    {/* Stats row */}
                    <div className="flex justify-between mt-4 pt-4 border-t border-border">
                        <div>
                            <p className="text-xs text-muted-foreground">Period High</p>
                            <p className="text-sm font-medium text-foreground">
                                {formatCurrency(data.summary.high)}
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Period Low</p>
                            <p className="text-sm font-medium text-foreground">
                                {formatCurrency(data.summary.low)}
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Data Points</p>
                            <p className="text-sm font-medium text-foreground">
                                {data.data_points}
                            </p>
                        </div>
                    </div>
                </>
            ) : (
                <div className="text-center py-16 text-muted-foreground">
                    <p>No historical data available</p>
                    <p className="text-xs mt-1">Portfolio snapshots will appear here over time</p>
                </div>
            )}
        </NeoCard>
    );
}
