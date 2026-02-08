"use client";

import React, { useState, useEffect } from "react";
import { NeoCard } from "@/components/ui/neo-card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Zap, Plus, Clock, TrendingUp, TrendingDown, RefreshCw, Pause, Play, Trash2, Settings, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { automationsApi } from "@/lib/api";
import { CreateAutomationModal } from "@/components/automations/CreateAutomationModal";

interface Automation {
    id: string;
    automation_type: string;
    name: string;
    status: string;
    source_token: string;
    dest_token: string;
    amount: number;
    frequency_seconds: number;
    next_execution_at: string;
    created_at: string;
}

const typeConfig: Record<string, { icon: React.ElementType; bgColor: string; textColor: string }> = {
    "dca": { icon: RefreshCw, bgColor: "bg-blue-100 dark:bg-blue-500/20", textColor: "text-blue-700 dark:text-blue-400" },
    "stop_loss": { icon: TrendingDown, bgColor: "bg-amber-100 dark:bg-amber-500/20", textColor: "text-amber-700 dark:text-amber-400" },
    "take_profit": { icon: TrendingUp, bgColor: "bg-emerald-100 dark:bg-emerald-500/20", textColor: "text-emerald-700 dark:text-emerald-400" },
    "rebalance": { icon: RefreshCw, bgColor: "bg-purple-100 dark:bg-purple-500/20", textColor: "text-purple-700 dark:text-purple-400" },
    "recurring_swap": { icon: RefreshCw, bgColor: "bg-blue-100 dark:bg-blue-500/20", textColor: "text-blue-700 dark:text-blue-400" },
};

const mockAutomations: Automation[] = [
    {
        id: "1",
        automation_type: "dca",
        name: "Daily SOL Accumulation",
        status: "active",
        source_token: "USDC",
        dest_token: "SOL",
        amount: 100,
        frequency_seconds: 86400,
        next_execution_at: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString(),
    },
    {
        id: "2",
        automation_type: "stop_loss",
        name: "SOL Protection",
        status: "active",
        source_token: "SOL",
        dest_token: "USDC",
        amount: 10,
        frequency_seconds: 0,
        next_execution_at: "",
        created_at: new Date().toISOString(),
    },
];

export default function AutomationsPage() {
    const [automationList, setAutomationList] = useState<Automation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);

    useEffect(() => {
        fetchAutomations();
    }, []);

    async function fetchAutomations() {
        setLoading(true);
        try {
            const response = await automationsApi.getAutomations();
            setAutomationList(response?.automations || []);
        } catch (err) {
            console.error('Failed to fetch automations:', err);
            setError('Failed to load automations. Showing sample data.');
            setAutomationList(mockAutomations);
        } finally {
            setLoading(false);
        }
    }

    const toggleStatus = async (id: string, currentStatus: string) => {
        setActionLoading(id);
        try {
            if (currentStatus === "active") {
                await automationsApi.pauseAutomation(id);
            } else {
                await automationsApi.resumeAutomation(id);
            }
            // Update local state
            setAutomationList(prev => prev.map(a =>
                a.id === id ? { ...a, status: a.status === "active" ? "paused" : "active" } : a
            ));
        } catch (err) {
            console.error('Failed to toggle automation:', err);
            // Toggle locally anyway for demo
            setAutomationList(prev => prev.map(a =>
                a.id === id ? { ...a, status: a.status === "active" ? "paused" : "active" } : a
            ));
        } finally {
            setActionLoading(null);
        }
    };

    const deleteAutomation = async (id: string) => {
        setActionLoading(id);
        try {
            await automationsApi.deleteAutomation(id);
            setAutomationList(prev => prev.filter(a => a.id !== id));
        } catch (err) {
            console.error('Failed to delete automation:', err);
            // Remove locally anyway for demo
            setAutomationList(prev => prev.filter(a => a.id !== id));
        } finally {
            setActionLoading(null);
        }
    };

    const formatFrequency = (seconds: number) => {
        if (seconds === 0) return "Trigger-based";
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
        return `${Math.floor(seconds / 86400)}d`;
    };

    const formatTimeUntil = (isoString: string) => {
        if (!isoString) return "";
        const target = new Date(isoString);
        const now = new Date();
        const diff = target.getTime() - now.getTime();
        if (diff <= 0) return "Now";
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        if (hours > 24) return `${Math.floor(hours / 24)}d`;
        return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    };

    const activeCount = automationList.filter(a => a.status === "active").length;
    const pausedCount = automationList.filter(a => a.status === "paused").length;

    const getTypeConfig = (type: string) => {
        return typeConfig[type] || typeConfig["dca"];
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Automations</h1>
                    <p className="text-muted-foreground">Manage your trading rules and strategies</p>
                </div>
                <Button
                    className="bg-primary hover:bg-primary/90 text-primary-foreground"
                    onClick={() => setShowCreateModal(true)}
                >
                    <Plus className="h-4 w-4 mr-2" />
                    New Automation
                </Button>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="p-3 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-lg">
                    <p className="text-sm text-amber-700 dark:text-amber-400">{error}</p>
                </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <NeoCard className="p-5">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">Active</p>
                            <h3 className="text-2xl font-bold text-foreground mt-1">{loading ? '...' : activeCount}</h3>
                        </div>
                        <div className="p-3 bg-emerald-100 dark:bg-emerald-500/20 rounded-xl">
                            <Play className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                        </div>
                    </div>
                </NeoCard>
                <NeoCard className="p-5">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">Paused</p>
                            <h3 className="text-2xl font-bold text-foreground mt-1">{loading ? '...' : pausedCount}</h3>
                        </div>
                        <div className="p-3 bg-amber-100 dark:bg-amber-500/20 rounded-xl">
                            <Pause className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                        </div>
                    </div>
                </NeoCard>
                <NeoCard className="p-5">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">Total</p>
                            <h3 className="text-2xl font-bold text-foreground mt-1">{loading ? '...' : automationList.length}</h3>
                        </div>
                        <div className="p-3 bg-blue-100 dark:bg-blue-500/20 rounded-xl">
                            <Zap className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                        </div>
                    </div>
                </NeoCard>
                <NeoCard className="p-5">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">DCA Strategies</p>
                            <h3 className="text-2xl font-bold text-foreground mt-1">
                                {loading ? '...' : automationList.filter(a => a.automation_type === 'dca').length}
                            </h3>
                        </div>
                        <div className="p-3 bg-purple-100 dark:bg-purple-500/20 rounded-xl">
                            <RefreshCw className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                        </div>
                    </div>
                </NeoCard>
            </div>

            {/* Quick Create */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {Object.entries(typeConfig).slice(0, 4).map(([type, config]) => {
                    const Icon = config.icon;
                    return (
                        <NeoCard key={type} className="p-4 cursor-pointer hover:border-primary/50 transition-all group">
                            <div className="flex items-center gap-3">
                                <div className={cn("p-2 rounded-lg", config.bgColor)}>
                                    <Icon className={cn("h-5 w-5", config.textColor)} />
                                </div>
                                <div>
                                    <p className="font-medium text-foreground group-hover:text-primary transition-colors capitalize">
                                        {type.replace('_', ' ')}
                                    </p>
                                    <p className="text-xs text-muted-foreground">Create new</p>
                                </div>
                            </div>
                        </NeoCard>
                    );
                })}
            </div>

            {/* Automations List */}
            <NeoCard className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="font-semibold text-foreground flex items-center gap-2">
                        <Zap className="h-5 w-5 text-primary" />
                        Your Automations
                    </h3>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : automationList.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                        <Zap className="h-12 w-12 mx-auto mb-4 opacity-30" />
                        <p>No automations yet</p>
                        <Button variant="link" className="mt-2">Create your first automation</Button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {automationList.map((automation) => {
                            const typeInfo = getTypeConfig(automation.automation_type);
                            const Icon = typeInfo.icon;

                            return (
                                <div
                                    key={automation.id}
                                    className={cn(
                                        "p-4 border rounded-xl transition-all",
                                        automation.status === "active"
                                            ? "border-border bg-card hover:border-primary/30"
                                            : "border-border/50 bg-muted/30"
                                    )}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-start gap-4">
                                            <div className={cn("p-3 rounded-xl", typeInfo.bgColor)}>
                                                <Icon className={cn("h-5 w-5", typeInfo.textColor)} />
                                            </div>
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-2">
                                                    <h4 className="font-medium text-foreground">{automation.name}</h4>
                                                    <span className={cn(
                                                        "text-xs px-2 py-0.5 rounded-full font-medium uppercase",
                                                        typeInfo.bgColor, typeInfo.textColor
                                                    )}>
                                                        {automation.automation_type.replace('_', ' ')}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-muted-foreground">
                                                    {automation.source_token} → {automation.dest_token}
                                                </p>

                                                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                                    <span>
                                                        Amount: <strong className="text-foreground">${automation.amount}</strong>
                                                    </span>
                                                    <span>
                                                        Frequency: <strong className="text-foreground">{formatFrequency(automation.frequency_seconds)}</strong>
                                                    </span>
                                                    {automation.next_execution_at && (
                                                        <span className="flex items-center gap-1">
                                                            <Clock className="h-3 w-3" />
                                                            Next: <strong className="text-foreground">{formatTimeUntil(automation.next_execution_at)}</strong>
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3">
                                            {actionLoading === automation.id ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <>
                                                    <Switch
                                                        checked={automation.status === "active"}
                                                        onCheckedChange={() => toggleStatus(automation.id, automation.status)}
                                                    />
                                                    <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
                                                        <Settings className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="text-muted-foreground hover:text-destructive"
                                                        onClick={() => deleteAutomation(automation.id)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </NeoCard>

            {/* Create Automation Modal */}
            <CreateAutomationModal
                isOpen={showCreateModal}
                onClose={() => setShowCreateModal(false)}
                onSuccess={() => {
                    fetchAutomations();
                }}
            />
        </div>
    );
}
