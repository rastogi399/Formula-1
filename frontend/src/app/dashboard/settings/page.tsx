"use client";

import React, { useState } from "react";
import { NeoCard } from "@/components/ui/neo-card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    User, Bell, Shield, Palette, Wallet, Globe,
    Moon, Sun, ChevronRight, ExternalLink, Key,
    Smartphone, Mail, AlertTriangle, Plus, Clock, Trash2, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";

interface SessionKey {
    id: string;
    name: string;
    publicKey: string;
    maxPerTx: number;
    maxTotal: number;
    spent: number;
    expiresAt: string;
    isActive: boolean;
}

const mockSessionKeys: SessionKey[] = [
    {
        id: "1",
        name: "DCA Automation",
        publicKey: "Sess1...xK4j",
        maxPerTx: 50,
        maxTotal: 1000,
        spent: 350,
        expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        isActive: true,
    },
    {
        id: "2",
        name: "Stop-Loss Protection",
        publicKey: "Sess2...m9Pq",
        maxPerTx: 100,
        maxTotal: 500,
        spent: 0,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        isActive: true,
    },
];

export default function SettingsPage() {
    const { theme, setTheme } = useTheme();
    const [sessionKeys, setSessionKeys] = useState<SessionKey[]>(mockSessionKeys);
    const [showCreateModal, setShowCreateModal] = useState(false);

    const settingsSections = [
        {
            title: "Account",
            icon: User,
            items: [
                { label: "Email", value: "user@example.com", type: "text" },
                { label: "Display Name", value: "Solana Trader", type: "text" },
            ]
        },
        {
            title: "Security",
            icon: Shield,
            items: [
                { label: "Two-Factor Authentication", value: true, type: "toggle" },
                { label: "Transaction Signing", value: true, type: "toggle" },
                { label: "Session Timeout", value: "30 minutes", type: "select" },
            ]
        },
        {
            title: "Notifications",
            icon: Bell,
            items: [
                { label: "Price Alerts", value: true, type: "toggle" },
                { label: "Trade Confirmations", value: true, type: "toggle" },
                { label: "Automation Updates", value: true, type: "toggle" },
                { label: "Email Notifications", value: false, type: "toggle" },
            ]
        },
    ];

    const revokeSessionKey = (id: string) => {
        setSessionKeys(prev => prev.map(sk =>
            sk.id === id ? { ...sk, isActive: false } : sk
        ));
    };

    const deleteSessionKey = (id: string) => {
        setSessionKeys(prev => prev.filter(sk => sk.id !== id));
    };

    const formatExpiry = (isoString: string) => {
        const date = new Date(isoString);
        const now = new Date();
        const diff = date.getTime() - now.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        if (days <= 0) return "Expired";
        if (days === 1) return "1 day";
        return `${days} days`;
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-foreground">Settings</h1>
                <p className="text-muted-foreground">Manage your account preferences</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Settings */}
                <div className="lg:col-span-2 space-y-6">


                    {/* Session Keys Section */}
                    <NeoCard className="p-6">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <div className="p-3 bg-purple-100 dark:bg-purple-500/20 rounded-xl">
                                    <Key className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground">Session Keys</h3>
                                    <p className="text-sm text-muted-foreground">Manage auto-approval for automations</p>
                                </div>
                            </div>
                            <Button size="sm" className="bg-primary hover:bg-primary/90">
                                <Plus className="h-4 w-4 mr-2" />
                                Create Session Key
                            </Button>
                        </div>

                        {sessionKeys.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <Key className="h-12 w-12 mx-auto mb-4 opacity-30" />
                                <p>No session keys created</p>
                                <p className="text-sm">Create a session key to enable auto-approval for your automations</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {sessionKeys.map((sk) => (
                                    <div
                                        key={sk.id}
                                        className={cn(
                                            "p-4 border rounded-xl transition-all",
                                            sk.isActive ? "border-border bg-card" : "border-border/50 bg-muted/30 opacity-60"
                                        )}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="space-y-2">
                                                <div className="flex items-center gap-2">
                                                    <h4 className="font-medium text-foreground">{sk.name}</h4>
                                                    <span className={cn(
                                                        "text-xs px-2 py-0.5 rounded-full",
                                                        sk.isActive
                                                            ? "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400"
                                                            : "bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400"
                                                    )}>
                                                        {sk.isActive ? "Active" : "Revoked"}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-muted-foreground font-mono">{sk.publicKey}</p>

                                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                                    <span>
                                                        Per Tx: <strong className="text-foreground">${sk.maxPerTx}</strong>
                                                    </span>
                                                    <span>
                                                        Total: <strong className="text-foreground">${sk.maxTotal}</strong>
                                                    </span>
                                                    <span>
                                                        Spent: <strong className="text-foreground">${sk.spent}</strong>
                                                    </span>
                                                    <span className="flex items-center gap-1">
                                                        <Clock className="h-3 w-3" />
                                                        Expires: <strong className="text-foreground">{formatExpiry(sk.expiresAt)}</strong>
                                                    </span>
                                                </div>

                                                {/* Progress bar */}
                                                <div className="w-48">
                                                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-primary rounded-full"
                                                            style={{ width: `${Math.min((sk.spent / sk.maxTotal) * 100, 100)}%` }}
                                                        />
                                                    </div>
                                                    <p className="text-xs text-muted-foreground mt-1">
                                                        {((sk.spent / sk.maxTotal) * 100).toFixed(0)}% of limit used
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-2">
                                                {sk.isActive && (
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => revokeSessionKey(sk.id)}
                                                    >
                                                        Revoke
                                                    </Button>
                                                )}
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-muted-foreground hover:text-destructive"
                                                    onClick={() => deleteSessionKey(sk.id)}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-500/10 rounded-lg border border-blue-100 dark:border-blue-500/20">
                            <div className="flex items-start gap-2">
                                <Zap className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                                <div className="text-xs text-blue-700 dark:text-blue-400">
                                    <p className="font-medium">Auto-Approval with Session Keys</p>
                                    <p className="mt-1">Session keys allow automations to execute transactions without manual approval, within your defined spending limits.</p>
                                </div>
                            </div>
                        </div>
                    </NeoCard>

                    {/* Settings Sections */}
                    {settingsSections.map((section) => {
                        const Icon = section.icon;
                        return (
                            <NeoCard key={section.title} className="p-6">
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="p-3 bg-primary/10 rounded-xl">
                                        <Icon className="h-5 w-5 text-primary" />
                                    </div>
                                    <h3 className="font-semibold text-foreground">{section.title}</h3>
                                </div>
                                <div className="space-y-4">
                                    {section.items.map((item, i) => (
                                        <div key={i} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                                            <Label className="text-foreground">{item.label}</Label>
                                            {item.type === "toggle" ? (
                                                <Switch defaultChecked={item.value as boolean} />
                                            ) : item.type === "text" ? (
                                                <Input
                                                    defaultValue={item.value as string}
                                                    className="max-w-[200px] text-right"
                                                />
                                            ) : (
                                                <span className="text-sm text-muted-foreground">{item.value}</span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </NeoCard>
                        );
                    })}

                    {/* Danger Zone */}
                    <NeoCard className="p-6 border-destructive/30">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-3 bg-destructive/10 rounded-xl">
                                <AlertTriangle className="h-5 w-5 text-destructive" />
                            </div>
                            <h3 className="font-semibold text-destructive">Danger Zone</h3>
                        </div>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between py-3">
                                <div>
                                    <p className="text-foreground font-medium">Delete Account</p>
                                    <p className="text-sm text-muted-foreground">Permanently delete your account and all data</p>
                                </div>
                                <Button variant="destructive" size="sm">Delete</Button>
                            </div>
                        </div>
                    </NeoCard>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Connected Wallets */}
                    <NeoCard className="p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <Wallet className="h-5 w-5 text-primary" />
                            <h3 className="font-semibold text-foreground">Connected Wallets</h3>
                        </div>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                                        <span className="text-white text-xs font-bold">P</span>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-foreground">Phantom</p>
                                        <p className="text-xs text-muted-foreground">8xK4...j9Pm</p>
                                    </div>
                                </div>
                                <span className="text-xs text-emerald-500 font-medium">Active</span>
                            </div>
                            <Button variant="outline" className="w-full">
                                <Plus className="h-4 w-4 mr-2" />
                                Add Wallet
                            </Button>
                        </div>
                    </NeoCard>

                    {/* Quick Links */}
                    <NeoCard className="p-6">
                        <h3 className="font-semibold text-foreground mb-4">Quick Links</h3>
                        <div className="space-y-2">
                            {[
                                { label: "API Keys", icon: Key },
                                { label: "Mobile App", icon: Smartphone },
                                { label: "Help Center", icon: Globe },
                                { label: "Contact Support", icon: Mail },
                            ].map((link) => (
                                <button
                                    key={link.label}
                                    className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors text-left"
                                >
                                    <div className="flex items-center gap-3">
                                        <link.icon className="h-4 w-4 text-muted-foreground" />
                                        <span className="text-sm text-foreground">{link.label}</span>
                                    </div>
                                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                </button>
                            ))}
                        </div>
                    </NeoCard>

                    {/* Version Info */}
                    <NeoCard className="p-4">
                        <div className="text-center text-sm text-muted-foreground">
                            <p>Solana Copilot v1.0.0</p>
                            <a href="#" className="text-primary hover:underline flex items-center justify-center gap-1 mt-1">
                                View Changelog <ExternalLink className="h-3 w-3" />
                            </a>
                        </div>
                    </NeoCard>
                </div>
            </div>
        </div>
    );
}
