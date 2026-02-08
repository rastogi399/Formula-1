"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";
import { RiskColors } from "./RiskGauge";

interface RiskMetricCardProps {
    label: string;
    description: string;
    value: string;
    level: string;
    icon: LucideIcon;
    getRiskColor: (level: string) => RiskColors;
}

export function RiskMetricCard({ label, description, value, level, icon: Icon, getRiskColor }: RiskMetricCardProps) {
    const levelColors = getRiskColor(level);

    return (
        <div
            className={cn(
                "p-4 rounded-xl border transition-all hover:shadow-md",
                levelColors.bg, levelColors.border
            )}
        >
            <div className="flex items-start justify-between mb-2">
                <Icon className={cn("h-5 w-5", levelColors.text)} />
                <span className={cn(
                    "text-xs font-medium px-2 py-0.5 rounded-full capitalize",
                    levelColors.bg, levelColors.text
                )}>
                    {level}
                </span>
            </div>
            <p className="text-2xl font-bold text-foreground">{value}</p>
            <p className="text-sm text-muted-foreground mt-1">{label}</p>
            <p className="text-xs text-muted-foreground/70 mt-0.5">{description}</p>
        </div>
    );
}
