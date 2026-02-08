"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { X, RefreshCw, TrendingDown, TrendingUp, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { automationsApi } from "@/lib/api";

interface CreateAutomationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

type AutomationType = "dca" | "recurring_swap" | "rebalance";

const automationTypes: { type: AutomationType; label: string; icon: React.ElementType; description: string; color: string }[] = [
    { type: "dca", label: "DCA", icon: RefreshCw, description: "Dollar-cost averaging into a token", color: "bg-blue-100 text-blue-700 border-blue-200" },
    { type: "recurring_swap", label: "Recurring Swap", icon: RefreshCw, description: "Recurring swap into a token", color: "bg-blue-100 text-blue-700 border-blue-200" },
    { type: "rebalance", label: "Rebalance", icon: RefreshCw, description: "Rebalance your portfolio", color: "bg-blue-100 text-blue-700 border-blue-200" },
    { type: "rebalance", label: "Rebalance", icon: RefreshCw, description: "Maintain target allocation percentages", color: "bg-purple-100 text-purple-700 border-purple-200" },
];

const frequencies = [
    { label: "Every Hour", seconds: 3600 },
    { label: "Daily", seconds: 86400 },
    { label: "Weekly", seconds: 604800 },
    { label: "Monthly", seconds: 2592000 },
];

export function CreateAutomationModal({ isOpen, onClose, onSuccess }: CreateAutomationModalProps) {
    const [step, setStep] = useState(1);
    const [selectedType, setSelectedType] = useState<AutomationType | null>(null);
    const [name, setName] = useState("");
    const [sourceToken, setSourceToken] = useState("USDC");
    const [destToken, setDestToken] = useState("SOL");
    const [amount, setAmount] = useState("");
    const [frequency, setFrequency] = useState(86400);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (!selectedType || !name || !amount) {
            setError("Please fill in all required fields");
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            await automationsApi.createAutomation({
                automation_type: selectedType,
                name,
                source_token: sourceToken,
                dest_token: destToken,
                amount: parseFloat(amount),
                frequency_seconds: frequency,
            });

            onSuccess?.();
            handleClose();
        } catch (err) {
            console.error("Failed to create automation:", err);
            setError("Failed to create automation. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleClose = () => {
        setStep(1);
        setSelectedType(null);
        setName("");
        setSourceToken("USDC");
        setDestToken("SOL");
        setAmount("");
        setFrequency(86400);
        setError(null);
        onClose();
    };

    const nextStep = () => {
        if (step === 1 && selectedType) {
            setStep(2);
        }
    };

    const prevStep = () => {
        if (step === 2) {
            setStep(1);
        }
    };

    return (
        <>
            {/* Backdrop */}
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" onClick={handleClose} />

            {/* Modal */}
            <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg px-4">
                <div className="bg-background border border-border rounded-2xl shadow-2xl overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-border">
                        <div>
                            <h2 className="text-xl font-bold text-foreground">Create Automation</h2>
                            <p className="text-sm text-muted-foreground">Step {step} of 2</p>
                        </div>
                        <button onClick={handleClose} className="p-2 hover:bg-muted rounded-lg transition-colors">
                            <X className="h-5 w-5 text-muted-foreground" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-6">
                        {step === 1 && (
                            <div className="space-y-4">
                                <p className="text-sm text-muted-foreground mb-4">Select the type of automation you want to create:</p>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {automationTypes.map((item) => {
                                        const Icon = item.icon;
                                        return (
                                            <button
                                                key={item.type}
                                                onClick={() => setSelectedType(item.type)}
                                                className={cn(
                                                    "p-4 border rounded-xl text-left transition-all",
                                                    selectedType === item.type
                                                        ? "border-primary bg-primary/5 ring-2 ring-primary/20"
                                                        : "border-border hover:border-primary/30 hover:bg-muted/50"
                                                )}
                                            >
                                                <div className={cn("p-2 rounded-lg w-fit mb-3", item.color)}>
                                                    <Icon className="h-5 w-5" />
                                                </div>
                                                <p className="font-medium text-foreground">{item.label}</p>
                                                <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {step === 2 && (
                            <div className="space-y-5">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Automation Name</Label>
                                    <Input
                                        id="name"
                                        placeholder="e.g., Daily SOL Accumulation"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="sourceToken">From Token</Label>
                                        <Input
                                            id="sourceToken"
                                            placeholder="USDC"
                                            value={sourceToken}
                                            onChange={(e) => setSourceToken(e.target.value.toUpperCase())}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="destToken">To Token</Label>
                                        <Input
                                            id="destToken"
                                            placeholder="SOL"
                                            value={destToken}
                                            onChange={(e) => setDestToken(e.target.value.toUpperCase())}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="amount">Amount (USD)</Label>
                                    <Input
                                        id="amount"
                                        type="number"
                                        placeholder="100"
                                        value={amount}
                                        onChange={(e) => setAmount(e.target.value)}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label>Frequency</Label>
                                    <div className="grid grid-cols-2 gap-2">
                                        {frequencies.map((f) => (
                                            <button
                                                key={f.seconds}
                                                onClick={() => setFrequency(f.seconds)}
                                                className={cn(
                                                    "p-3 border rounded-lg text-sm font-medium transition-all",
                                                    frequency === f.seconds
                                                        ? "border-primary bg-primary/10 text-primary"
                                                        : "border-border text-muted-foreground hover:border-primary/30"
                                                )}
                                            >
                                                {f.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {error && (
                                    <div className="p-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg">
                                        <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="p-6 border-t border-border flex gap-3">
                        {step === 2 && (
                            <Button variant="outline" className="flex-1" onClick={prevStep}>
                                Back
                            </Button>
                        )}
                        {step === 1 ? (
                            <Button
                                className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground"
                                onClick={nextStep}
                                disabled={!selectedType}
                            >
                                Continue
                            </Button>
                        ) : (
                            <Button
                                className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground"
                                onClick={handleSubmit}
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    "Create Automation"
                                )}
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
}
