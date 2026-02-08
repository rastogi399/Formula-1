"use client";

import React from "react";
import { NeoCard } from "@/components/ui/neo-card";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface RiskColors {
    text: string;
    bg: string;
    border: string;
}

interface RiskGaugeProps {
    riskScore: number;
    riskLevel: string;
    loading?: boolean;
    getRiskColor: (level: string) => RiskColors;
}

export function RiskGauge({ riskScore, riskLevel, loading = false, getRiskColor }: RiskGaugeProps) {
    const riskColors = getRiskColor(riskLevel);

    return (
        <NeoCard className="lg:col-span-1 p-8 flex flex-col items-center justify-center">
            {loading ? (
                <Loader2 className="h-12 w-12 animate-spin text-muted-foreground" />
            ) : (
                <>
                    {/* Gauge */}
                    <div className="relative w-48 h-24 overflow-hidden mb-4">
                        <div className="absolute w-48 h-48 rounded-full border-[16px] border-muted" />
                        <div
                            className={cn(
                                "absolute w-48 h-48 rounded-full border-[16px] border-b-transparent border-r-transparent border-l-transparent transition-transform duration-500",
                                riskColors.text.replace("text-", "border-t-")
                            )}
                            style={{
                                transform: `rotate(${-90 + (riskScore / 100) * 180}deg)`,
                            }}
                        />
                    </div>
                    <div className="text-center">
                        <p className="text-5xl font-bold text-foreground">{riskScore}</p>
                        <p className="text-sm text-muted-foreground">out of 100</p>
                    </div>
                    <div className={cn(
                        "mt-4 px-4 py-2 rounded-full text-sm font-medium capitalize",
                        riskColors.bg, riskColors.text
                    )}>
                        {riskLevel.replace("_", " ")} Risk
                    </div>
                </>
            )}
        </NeoCard>
    );
}
