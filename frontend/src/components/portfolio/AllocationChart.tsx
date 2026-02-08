"use client";

import React from "react";
import { NeoCard } from "@/components/ui/neo-card";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';
import { CHART_COLORS, Holding } from "./HoldingsTable";

interface AllocationChartProps {
    holdings: Holding[];
}

export function AllocationChart({ holdings }: AllocationChartProps) {
    const chartData = holdings.map((h, i) => ({
        name: h.symbol,
        value: h.value_usd,
        fill: CHART_COLORS[i % CHART_COLORS.length],
    }));

    return (
        <NeoCard className="p-6">
            <h3 className="font-semibold text-foreground mb-6">Allocation</h3>
            <div className="h-[200px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.fill} stroke="none" />
                            ))}
                        </Pie>
                        <RechartsTooltip
                            contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                            itemStyle={{ color: 'hsl(var(--foreground))' }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
                {holdings.slice(0, 4).map((holding, index) => (
                    <div key={holding.mint} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }} />
                            <span className="text-foreground">{holding.symbol}</span>
                        </div>
                        <span className="text-muted-foreground">{holding.allocation_pct.toFixed(1)}%</span>
                    </div>
                ))}
            </div>
        </NeoCard>
    );
}
