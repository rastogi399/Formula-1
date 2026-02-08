"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps {
    className?: string;
}

/**
 * Base Skeleton component for loading states
 * Provides animated placeholder while content loads
 */
export function Skeleton({ className }: SkeletonProps) {
    return (
        <div
            className={cn(
                "animate-pulse rounded-md bg-muted",
                className
            )}
        />
    );
}

/**
 * Card skeleton for dashboard widgets
 */
export function CardSkeleton({ className }: SkeletonProps) {
    return (
        <div className={cn("p-6 rounded-2xl border border-border bg-card/50", className)}>
            <Skeleton className="h-4 w-24 mb-4" />
            <Skeleton className="h-8 w-32 mb-2" />
            <Skeleton className="h-3 w-16" />
        </div>
    );
}

/**
 * Table row skeleton
 */
export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
    return (
        <div className="flex items-center gap-4 p-4 border-b border-border">
            {Array.from({ length: columns }).map((_, i) => (
                <Skeleton
                    key={i}
                    className={cn(
                        "h-4",
                        i === 0 ? "w-8 rounded-full" : "flex-1"
                    )}
                />
            ))}
        </div>
    );
}

/**
 * Holdings list skeleton
 */
export function HoldingsListSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="space-y-2">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="flex items-center gap-4 p-3">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-3 w-16" />
                    </div>
                    <div className="text-right space-y-2">
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-3 w-12" />
                    </div>
                </div>
            ))}
        </div>
    );
}

/**
 * Chart skeleton
 */
export function ChartSkeleton({ className }: SkeletonProps) {
    return (
        <div className={cn("relative", className)}>
            <Skeleton className="h-full w-full rounded-xl" />
            <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-sm text-muted-foreground">Loading chart...</p>
            </div>
        </div>
    );
}

/**
 * Form skeleton
 */
export function FormSkeleton({ fields = 3 }: { fields?: number }) {
    return (
        <div className="space-y-4">
            {Array.from({ length: fields }).map((_, i) => (
                <div key={i} className="space-y-2">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-10 w-full" />
                </div>
            ))}
            <Skeleton className="h-10 w-32 mt-4" />
        </div>
    );
}

/**
 * Dashboard page skeleton
 */
export function DashboardSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div className="space-y-2">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-10 w-32" />
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {Array.from({ length: 4 }).map((_, i) => (
                    <CardSkeleton key={i} />
                ))}
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <div className="p-6 rounded-2xl border border-border bg-card/50">
                        <Skeleton className="h-5 w-32 mb-4" />
                        <ChartSkeleton className="h-64" />
                    </div>
                </div>
                <div className="p-6 rounded-2xl border border-border bg-card/50">
                    <Skeleton className="h-5 w-24 mb-4" />
                    <HoldingsListSkeleton rows={4} />
                </div>
            </div>
        </div>
    );
}
