"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
    ArrowUpRight, ArrowDownRight, TrendingUp, ShieldCheck, Activity,
    Clock, Loader2, Send, Sparkles, Wallet, BarChart3,
    ArrowRightLeft, Lock, ArrowDown, AlertTriangle, Pause, Trash2, Mic
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
    AreaChart, Area, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer,
    RadialBarChart, RadialBar
} from 'recharts';
import { portfolioApi, automationsApi, transactionsApi } from "@/lib/api";
import { useChatStore } from "@/store/useChatStore";
import { toast } from "sonner";

// --- Types ---
interface TokenHolding {
    mint: string;
    symbol: string;
    amount: number;
    price_usd: number;
    value_usd: number;
    allocation_pct: number;
    pnl_24h_pct?: number;
}

interface PortfolioRisk {
    risk_score: number;
    risk_level: string;
    volatility_90d_pct: number;
    max_drawdown_90d_pct: number;
    concentration_top3_pct: number;
}

interface Automation {
    id: string;
    automation_type: string;
    name: string;
    status: string;
    next_execution_at: string;
    source_token: string;
    dest_token: string;
    amount: number;
}

interface RecentActivity {
    id: string;
    action: string;
    description: string;
    status: string;
    timestamp: string;
    tx_signature: string | null;
}

// --- Components ---

const DashboardCard = ({ children, className, title, icon: Icon, action }: any) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn("bg-card border-2 border-border rounded-xl overflow-hidden flex flex-col shadow-sm", className)}
    >
        {(title || Icon) && (
            <div className="p-5 border-b border-border flex justify-between items-center bg-muted/30">
                <div className="flex items-center gap-2">
                    {Icon && <Icon className="h-5 w-5 text-primary" />}
                    <h3 className="font-semibold text-foreground font-grotesk">{title}</h3>
                </div>
                {action}
            </div>
        )}
        <div className="p-5 flex-1 relative">
            {children}
        </div>
    </motion.div>
);

const ChatMessage = ({ role, text }: any) => (
    <div className={cn("flex w-full mb-4", role === "user" ? "justify-end" : "justify-start")}>
        <div className={cn(
            "max-w-[85%] p-3 rounded-2xl text-sm leading-relaxed",
            role === "user"
                ? "bg-primary text-primary-foreground rounded-br-sm"
                : "bg-muted text-foreground border border-border rounded-bl-sm"
        )}>
            {role === "assistant" && (
                <div className="flex items-center gap-2 mb-1 text-primary text-xs font-bold uppercase tracking-wider">
                    <Sparkles className="h-3 w-3" /> Copilot
                </div>
            )}
            {text}
        </div>
    </div>
);

export default function DashboardPage() {
    // --- State ---
    const [portfolio, setPortfolio] = useState<{ total_usd: number; change_pct: number } | null>(null);
    const [holdings, setHoldings] = useState<TokenHolding[]>([]);
    const [risk, setRisk] = useState<PortfolioRisk | null>(null);
    const [automations, setAutomations] = useState<Automation[]>([]);
    const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
    const [loading, setLoading] = useState(true);

    // Chat State
    const { messages, isLoading: isChatLoading, sendMessage } = useChatStore();
    const [chatInput, setChatInput] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // --- Effects ---
    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            try {
                const [portfolioRes, holdingsRes, riskRes, automationsRes, activityRes] = await Promise.allSettled([
                    portfolioApi.getPortfolio(),
                    portfolioApi.getHoldings(),
                    portfolioApi.getRisk(),
                    automationsApi.getAutomations('active'),
                    transactionsApi.getRecentActivity(5),
                ]);

                if (portfolioRes.status === 'fulfilled') {
                    setPortfolio({
                        total_usd: portfolioRes.value.portfolio_summary?.total_usd || 15234.50,
                        change_pct: portfolioRes.value.performance?.return_1d_pct || 2.1,
                    });
                }
                if (holdingsRes.status === 'fulfilled') setHoldings(holdingsRes.value || []);
                if (riskRes.status === 'fulfilled') setRisk(riskRes.value);
                if (automationsRes.status === 'fulfilled') setAutomations(automationsRes.value?.automations || []);
                if (activityRes.status === 'fulfilled') setRecentActivity(activityRes.value?.activity || []);

            } catch (error) {
                console.error("Failed to fetch dashboard data", error);
                toast.error("Failed to load some dashboard data");
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // --- Handlers ---
    const handleSendMessage = async () => {
        if (!chatInput.trim()) return;
        await sendMessage(chatInput);
        setChatInput("");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Mock chart data if API doesn't provide history yet
    const portfolioChartData = [
        { name: 'Mon', value: 14200 },
        { name: 'Tue', value: 14500 },
        { name: 'Wed', value: 14350 },
        { name: 'Thu', value: 14800 },
        { name: 'Fri', value: 15100 },
        { name: 'Sat', value: 14900 },
        { name: 'Sun', value: 15000 },
    ];

    // Fallback data for display
    const displayPortfolio = portfolio || { total_usd: 15234.50, change_pct: 2.1 };
    const displayHoldings = holdings.length > 0 ? holdings : [
        { mint: "SOL", symbol: "SOL", amount: 145.2, price_usd: 72.50, value_usd: 10527, allocation_pct: 70.2, pnl_24h_pct: 12.5 },
        { mint: "USDC", symbol: "USDC", amount: 3500, price_usd: 1.00, value_usd: 3500, allocation_pct: 23.3, pnl_24h_pct: 0.01 },
    ];
    const displayRisk = risk || { risk_score: 45, risk_level: "medium", volatility_90d_pct: 8.5, max_drawdown_90d_pct: 12.3, concentration_top3_pct: 95.8 };

    return (
        <div className="min-h-screen font-sans p-4 md:p-8 text-foreground">


            {/* --- LEFT COLUMN (Main Content) --- */}
            <div className="lg:col-span-8 space-y-6">

                {/* Top Row: Portfolio Value (Hero) */}
                <DashboardCard className="min-h-[320px] relative overflow-hidden">
                    <div className="flex justify-between items-start z-10 relative">
                        <div>
                            <p className="text-muted-foreground font-medium mb-1">Total Portfolio Value</p>
                            {loading ? (
                                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                            ) : (
                                <h1 className="text-5xl font-bold font-grotesk text-foreground mb-2">
                                    ${displayPortfolio.total_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </h1>
                            )}
                            <div className="flex items-center gap-2">
                                <span className={cn(
                                    "px-2 py-1 rounded-md text-sm font-bold flex items-center gap-1",
                                    displayPortfolio.change_pct >= 0 ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                                )}>
                                    {displayPortfolio.change_pct >= 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                                    {Math.abs(displayPortfolio.change_pct).toFixed(2)}%
                                </span>
                                <span className="text-muted-foreground text-sm">vs last 24h</span>
                            </div>
                        </div>
                        <div className="text-right hidden sm:block">
                            <p className="text-muted-foreground text-xs">Last updated: Just now</p>
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="absolute bottom-0 left-0 right-0 h-48 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={portfolioChartData}>
                                <defs>
                                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <Area type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </DashboardCard>

                {/* Middle Row: Holdings & Performance & Risk */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Holdings */}
                    <DashboardCard title="Holdings" icon={Wallet} className="md:col-span-1">
                        <div className="space-y-4">
                            {loading ? <Loader2 className="mx-auto animate-spin" /> : displayHoldings.slice(0, 4).map((token) => (
                                <div key={token.mint} className="flex justify-between items-center group cursor-pointer hover:bg-muted/50 p-2 rounded-lg transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className="w-1 h-8 bg-border group-hover:bg-primary transition-colors rounded-full" />
                                        <div>
                                            <p className="font-bold">{token.symbol}</p>
                                            <p className="text-xs text-muted-foreground">{token.amount.toLocaleString()} Tokens</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold">${token.value_usd.toLocaleString()}</p>
                                        <p className={cn("text-xs", (token.pnl_24h_pct || 0) >= 0 ? "text-emerald-500" : "text-red-500")}>
                                            {(token.pnl_24h_pct || 0) >= 0 ? "+" : ""}{(token.pnl_24h_pct || 0).toFixed(2)}%
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <Button variant="ghost" className="w-full mt-4 text-xs text-muted-foreground hover:text-foreground">View All Holdings</Button>
                    </DashboardCard>

                    {/* Performance */}
                    <DashboardCard title="Performance" icon={BarChart3} className="md:col-span-1">
                        <div className="grid grid-cols-2 gap-4 h-full content-center">
                            <div className="p-3 bg-muted/30 rounded-lg border border-border">
                                <p className="text-xs text-muted-foreground mb-1">Total PnL</p>
                                <p className="text-lg font-bold text-emerald-500">+$2,000</p>
                            </div>
                            <div className="p-3 bg-muted/30 rounded-lg border border-border">
                                <p className="text-xs text-muted-foreground mb-1">Realized</p>
                                <p className="text-lg font-bold text-foreground">+$500</p>
                            </div>
                            <div className="p-3 bg-muted/30 rounded-lg border border-border">
                                <p className="text-xs text-muted-foreground mb-1">Unrealized</p>
                                <p className="text-lg font-bold text-foreground">+$1,500</p>
                            </div>
                            <div className="p-3 bg-muted/30 rounded-lg border border-border">
                                <p className="text-xs text-muted-foreground mb-1">30d Return</p>
                                <p className="text-lg font-bold text-primary">+12.1%</p>
                            </div>
                        </div>
                    </DashboardCard>

                    {/* Risk Gauge */}
                    <DashboardCard title="Risk Score" icon={ShieldCheck} className="md:col-span-1">
                        <div className="flex flex-col items-center justify-center h-full">
                            <div className="relative w-32 h-32 flex items-center justify-center">
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadialBarChart
                                        innerRadius="80%"
                                        outerRadius="100%"
                                        barSize={10}
                                        data={[{ name: 'risk', value: displayRisk.risk_score, fill: '#FBBF24' }]}
                                        startAngle={180}
                                        endAngle={0}
                                    >
                                        <RadialBar background dataKey="value" cornerRadius={10} />
                                    </RadialBarChart>
                                </ResponsiveContainer>
                                <div className="absolute inset-0 flex flex-col items-center justify-center pt-8">
                                    <span className="text-3xl font-bold text-foreground">{displayRisk.risk_score}</span>
                                    <span className="text-xs text-amber-500 font-bold uppercase">{displayRisk.risk_level} Risk</span>
                                </div>
                            </div>
                            <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg w-full">
                                <p className="text-xs text-amber-500 flex items-start gap-2">
                                    <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0" />
                                    {displayRisk.concentration_top3_pct > 70 ? "High concentration. Consider rebalancing." : "Portfolio looks healthy."}
                                </p>
                            </div>
                        </div>
                    </DashboardCard>
                </div>

                {/* Bottom Row: Transactions & Automations */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Recent Transactions */}
                    <DashboardCard title="Recent Transactions" icon={Activity} className="md:col-span-2">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-muted-foreground uppercase bg-muted/30">
                                    <tr>
                                        <th className="px-4 py-3 rounded-l-lg">Action</th>
                                        <th className="px-4 py-3">Description</th>
                                        <th className="px-4 py-3">Status</th>
                                        <th className="px-4 py-3 rounded-r-lg">Time</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {loading ? (
                                        <tr><td colSpan={4} className="p-4 text-center"><Loader2 className="animate-spin mx-auto" /></td></tr>
                                    ) : recentActivity.length > 0 ? recentActivity.map((tx) => (
                                        <tr key={tx.id} className="hover:bg-muted/30 transition-colors">
                                            <td className="px-4 py-3 font-medium flex items-center gap-2">
                                                <div className="p-1.5 bg-muted rounded-md text-foreground">
                                                    <Activity className="h-3 w-3" />
                                                </div>
                                                {tx.action}
                                            </td>
                                            <td className="px-4 py-3 text-muted-foreground">{tx.description}</td>
                                            <td className="px-4 py-3">
                                                <span className={cn(
                                                    "px-2 py-1 rounded-full text-xs font-bold",
                                                    tx.status === "success" ? "bg-emerald-500/10 text-emerald-500" :
                                                        tx.status === "pending" ? "bg-amber-500/10 text-amber-500" :
                                                            "bg-red-500/10 text-red-500"
                                                )}>
                                                    {tx.status}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-muted-foreground text-xs">{new Date(tx.timestamp).toLocaleTimeString()}</td>
                                        </tr>
                                    )) : (
                                        <tr><td colSpan={4} className="p-4 text-center text-muted-foreground">No recent transactions</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                        <div className="mt-4 text-center">
                            <a href="#" className="text-sm text-primary hover:underline">View All Transactions</a>
                        </div>
                    </DashboardCard>

                    {/* Active Automations */}
                    <DashboardCard title="Active Automations" icon={Clock} className="md:col-span-1">
                        <div className="space-y-4">
                            {loading ? <Loader2 className="mx-auto animate-spin" /> : automations.length > 0 ? automations.map((auto) => (
                                <div key={auto.id} className="p-4 bg-muted/30 border border-border rounded-xl hover:border-primary/50 transition-all group">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-xs font-bold bg-primary/20 text-primary px-2 py-0.5 rounded-md">
                                            {auto.automation_type}
                                        </span>
                                        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button className="text-muted-foreground hover:text-foreground"><Pause className="h-3 w-3" /></button>
                                            <button className="text-muted-foreground hover:text-destructive"><Trash2 className="h-3 w-3" /></button>
                                        </div>
                                    </div>
                                    <h4 className="font-bold text-sm mb-1">{auto.name}</h4>
                                    <div className="flex justify-between items-center text-xs text-muted-foreground border-t border-border pt-2 mt-2">
                                        <span>Next: {new Date(auto.next_execution_at).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            )) : (
                                <div className="text-center py-8 text-muted-foreground">No active automations</div>
                            )}
                        </div>
                        <Button className="w-full mt-4 bg-muted hover:bg-muted/80 text-foreground border border-transparent hover:border-primary transition-all">
                            + Create Automation
                        </Button>
                    </DashboardCard>
                </div>
            </div>




        </div>
    );
}
