"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles, Shield, Zap, TrendingUp, Activity, Check, Lock, Terminal } from "lucide-react";
import HeroChatPreview from "@/components/landing/HeroChatPreview";
import { motion } from "framer-motion";

const features = [
    {
        title: "Smart Contract Automation",
        icon: <Sparkles className="h-8 w-8 text-black" />,
        description: "Deploy and interact with audited smart contracts to automate trades and strategies on Ethereum and EVM chains.",
        color: "bg-primary",
    },
    {
        title: "Portfolio Analytics & Risk Engine",
        icon: <TrendingUp className="h-8 w-8 text-black" />,
        description: "Real-time PnL, volatility, drawdown, and AI-powered risk insights that inform automated rebalancing and hedging.",
        color: "bg-secondary",
    },
    {
        title: "AI Reasoning & Automation",
        icon: <Activity className="h-8 w-8 text-black" />,
        description: "Natural language automation powered by an autonomous AI agent that plans, simulates, and executes multi-chain strategies.",
        color: "bg-white",
    },
];

const trustPoints = [
    {
        title: "Sign-only authentication",
        description: "You keep custody: keys never leave your device; Schumacher only requests signed transactions.",
        icon: <Lock className="h-6 w-6 text-primary" />,
    },
    {
        title: "On-chain Simulation & Safety",
        description: "Every automation is pre-simulated and validated against on-chain state to reduce execution risk.",
        icon: <Terminal className="h-6 w-6 text-primary" />,
    },
    {
        title: "Explainable AI",
        description: "Transparent AI reasoning shows why actions are recommended and what the expected outcomes are.",
        icon: <Sparkles className="h-6 w-6 text-primary" />,
    },
];

const protocols = ["Jupiter", "Orca", "Raydium", "Marinade", "Magic Eden", "Birdeye"];

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-white relative overflow-hidden flex flex-col font-sans text-black">
            {/* Navbar */}
            <header className="fixed top-0 w-full z-50 border-b-4 border-black bg-white">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary border-2 border-black flex items-center justify-center shadow-[4px_4px_0px_#000000]">
                            <Sparkles className="text-white h-6 w-6" />
                        </div>
                        <span className="font-bold text-2xl tracking-tight">Schumacher</span>
                    </div>
                    <nav className="hidden md:flex items-center gap-8">
                        <Link href="#features" className="text-base font-bold hover:text-primary transition-colors uppercase tracking-wide">Services</Link>
                        <Link href="#trust" className="text-base font-bold hover:text-primary transition-colors uppercase tracking-wide">Security</Link>
                        <Link href="#pricing" className="text-base font-bold hover:text-primary transition-colors uppercase tracking-wide">Subscriptions</Link>
                    </nav>
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard">
                            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground border-2 border-black shadow-[4px_4px_0px_#000000] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_#000000] transition-all font-bold text-base h-12 px-6 rounded-none focus:ring-primary focus:outline-none">
                                Launch App
                            </Button>
                        </Link>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="pt-40 pb-20 px-6 relative z-10">
                <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        className="space-y-8"
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 border-2 border-black text-black text-sm font-bold uppercase tracking-wider shadow-[4px_4px_0px_#000000]">
                            <Sparkles className="h-4 w-4" />
                            <span>AI-Powered DeFi Automation</span>
                        </div>
                        <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold leading-[1.04] tracking-tight text-white">
                            Your Autonomous AI DeFi Agent
                        </h1>
                        <p className="text-lg text-gray-600 max-w-lg leading-relaxed font-medium">
                            Trade, automate, and manage portfolios across Ethereum and Solana using natural language.
                        </p>
                        <p className="text-xl text-gray-600 max-w-lg leading-relaxed font-medium border-l-4 border-secondary pl-6">
                            Execute swaps, track portfolios, and automate strategies using smart contracts and conversational AI — without giving up custody of your assets.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 pt-4">
                            <Link href="/dashboard">
                                <Button size="lg" className="bg-primary hover:bg-primary/90 text-primary-foreground border-2 border-black shadow-[6px_6px_0px_#000000] hover:translate-y-[-2px] hover:shadow-[8px_8px_0px_#000000] transition-all font-bold text-lg h-14 px-10 rounded-none w-full sm:w-auto focus:ring-primary focus:outline-none">
                                    Connect Wallet <ArrowRight className="ml-2 h-5 w-5" />
                                </Button>
                            </Link>
                        </div>
                    </motion.div>

                    {/* Hero Visual - Animated Chat Preview */}
                    <HeroChatPreview />
                </div>
            </section>

            {/* Feature Grid (Bento) */}
            <section id="features" className="py-24 px-6 bg-gray-50 border-t-4 border-black">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl md:text-5xl font-extrabold mb-6 text-white">Power features for professional DeFi automation</h2>
                        <p className="text-xl text-gray-600 max-w-2xl mx-auto font-medium">
                            Smart contracts, autonomous execution, and analytics to power institutional-grade automation.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {features.map((feature, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 50 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.1, duration: 0.5 }}
                                whileHover={{ y: -8 }}
                                className={`p-8 border-4 border-black shadow-[8px_8px_0px_#000000] hover:shadow-[12px_12px_0px_#ff6a00] transition-all bg-white flex flex-col h-full`}
                            >
                                <div className={`w-16 h-16 ${feature.color} border-2 border-black flex items-center justify-center mb-6 shadow-[4px_4px_0px_#000000]`}>
                                    {feature.icon}
                                </div>
                                <h3 className="text-2xl font-bold mb-4">{feature.title}</h3>
                                <p className="text-gray-700 leading-relaxed font-medium">
                                    {feature.description}
                                </p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Trust Section */}
            <section id="trust" className="py-24 px-6 border-t-4 border-black">
                <div className="max-w-7xl mx-auto">
                    <div className="border-4 border-black bg-white p-10 md:p-16 shadow-[12px_12px_0px_#000000]">
                        <div className="text-center mb-12">
                            <h2 className="text-4xl font-bold mb-4">Non-Custodial & Transparent</h2>
                            <div className="w-24 h-2 bg-primary mx-auto"></div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                            {trustPoints.map((point, index) => (
                                <div key={index} className="flex flex-col items-center text-center space-y-4">
                                    <div className="w-16 h-16 bg-black rounded-full flex items-center justify-center mb-2">
                                        <div className="text-white">{point.icon}</div>
                                    </div>
                                    <h3 className="text-xl font-bold">{point.title}</h3>
                                    <p className="text-gray-600 font-medium">{point.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* Social Proof */}
            <section className="py-16 px-6 bg-black text-white border-t-4 border-black">
                <div className="max-w-7xl mx-auto text-center">
                    <p className="text-gray-400 font-bold uppercase tracking-widest mb-10 text-sm">Powered by Ethereum, Solana, and leading DeFi protocols</p>
                    <div className="flex flex-wrap justify-center gap-8 md:gap-16 opacity-80">
                        {protocols.map((protocol, index) => (
                            <span key={index} className="text-2xl md:text-3xl font-bold font-mono hover:text-primary transition-colors cursor-default">
                                {protocol}
                            </span>
                        ))}
                    </div>
                </div>
            </section>

            {/* Pricing/Waitlist */}
            <section id="pricing" className="py-24 px-6 bg-primary border-t-4 border-black">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="bg-white border-4 border-black p-10 md:p-16 shadow-[16px_16px_0px_#000000]">
                        <h2 className="text-5xl md:text-6xl font-bold mb-6">Experience Autonomous DeFi Trading</h2>
                        <p className="text-xl text-gray-700 mb-10 font-medium">
                            Automate strategies, analyze portfolios, and execute trades across Ethereum and Solana using AI.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto">
                            <input
                                type="email"
                                placeholder="Enter your email"
                                className="flex-1 h-14 px-6 border-2 border-black bg-gray-50 text-lg font-medium outline-none focus:bg-white transition-colors placeholder:text-gray-400"
                            />
                            <Button className="h-14 px-8 bg-black text-white hover:bg-gray-900 border-2 border-black font-bold text-lg rounded-none">
                                Get Early Access
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 px-6 bg-white border-t-4 border-black">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary border-2 border-black flex items-center justify-center">
                            <Sparkles className="text-white h-4 w-4" />
                        </div>
                        <span className="font-bold text-xl">Schumacher</span>
                    </div>
                    <div className="flex items-center gap-8 font-bold text-sm uppercase tracking-wide">
                        <Link href="#" className="hover:text-primary transition-colors">Privacy</Link>
                        <Link href="#" className="hover:text-primary transition-colors">Terms</Link>
                        <Link href="#" className="hover:text-primary transition-colors">Twitter</Link>
                        <Link href="#" className="hover:text-primary transition-colors">Discord</Link>
                    </div>
                    <p className="text-sm font-medium text-gray-500">© {new Date().getFullYear()} Schumacher.</p>
                </div>
            </footer>
        </div>
    );
}
