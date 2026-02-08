import React from 'react';
import { Button } from "@/components/ui/button";
import { NeoCard } from "@/components/ui/neo-card";
import { ArrowRight, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export interface TransactionDetails {
    type: 'swap' | 'send' | 'stake';
    fromToken: string;
    fromAmount: string;
    toToken: string;
    toAmount: string;
    priceImpact?: string;
    fee: string;
    route?: string;
    riskLevel?: 'low' | 'medium' | 'high';
    swapTransaction?: string;
}

interface TransactionPreviewProps {
    details: TransactionDetails;
    onApprove: () => void;
    onReject: () => void;
}

export function TransactionPreview({ details, onApprove, onReject }: TransactionPreviewProps) {
    return (
        <NeoCard className="p-4 w-full max-w-sm mt-2 border-primary/20 bg-primary/5">
            <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm text-foreground uppercase tracking-wider">{details.type} Preview</h4>
                {details.riskLevel && (
                    <div className={cn(
                        "flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium",
                        details.riskLevel === 'low' ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400" :
                            details.riskLevel === 'medium' ? "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400" :
                                "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400"
                    )}>
                        <AlertTriangle className="h-3 w-3" />
                        {details.riskLevel.charAt(0).toUpperCase() + details.riskLevel.slice(1)} Risk
                    </div>
                )}
            </div>

            <div className="flex items-center justify-between gap-2 mb-4">
                <div className="bg-background p-2 rounded-lg border border-border flex-1 text-center">
                    <p className="text-lg font-bold text-foreground">{details.fromAmount}</p>
                    <p className="text-xs text-muted-foreground">{details.fromToken}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <div className="bg-background p-2 rounded-lg border border-border flex-1 text-center">
                    <p className="text-lg font-bold text-foreground">{details.toAmount}</p>
                    <p className="text-xs text-muted-foreground">{details.toToken}</p>
                </div>
            </div>

            <div className="space-y-2 text-xs text-muted-foreground mb-4 bg-muted/30 p-2 rounded-lg">
                <div className="flex justify-between">
                    <span>Route</span>
                    <span className="font-medium text-foreground">{details.route || 'Best Route'}</span>
                </div>
                <div className="flex justify-between">
                    <span>Network Fee</span>
                    <span className="font-medium text-foreground">{details.fee}</span>
                </div>
                {details.priceImpact && (
                    <div className="flex justify-between">
                        <span>Price Impact</span>
                        <span className={cn(
                            "font-medium",
                            parseFloat(details.priceImpact) > 1 ? "text-red-500" : "text-emerald-500"
                        )}>{details.priceImpact}</span>
                    </div>
                )}
            </div>

            <div className="flex gap-2">
                <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 dark:border-red-900/50 dark:text-red-400 dark:hover:bg-red-900/20"
                    onClick={onReject}
                >
                    <XCircle className="h-4 w-4 mr-1" />
                    Reject
                </Button>
                <Button
                    size="sm"
                    className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground"
                    onClick={onApprove}
                >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Approve
                </Button>
            </div>
        </NeoCard>
    );
}
