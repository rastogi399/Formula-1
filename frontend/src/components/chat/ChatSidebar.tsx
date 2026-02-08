"use client";

import React, { useState } from "react";
import { Send, Sparkles, X, MessageCircle, Mic } from "lucide-react";
import { TransactionPreview, TransactionDetails } from "./TransactionPreview";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/store/useChatStore";
import { useConnection, useWallet } from '@solana/wallet-adapter-react';
import { VersionedTransaction } from '@solana/web3.js';
import { toast } from 'sonner';

interface ChatWidgetProps {
    isOpen: boolean;
    onToggle: () => void;
}

export function ChatWidget({ isOpen, onToggle }: ChatWidgetProps) {
    const [input, setInput] = useState("");
    const { messages, isLoading, sendMessage } = useChatStore();
    const messagesEndRef = React.useRef<HTMLDivElement>(null);

    const { connection } = useConnection();
    const { publicKey, signTransaction } = useWallet();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    React.useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;
        const message = input;
        setInput("");
        await sendMessage(message);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleApprove = async (details: TransactionDetails) => {
        if (!details.swapTransaction) {
            toast.error("No transaction data found");
            return;
        }

        if (!publicKey || !signTransaction) {
            toast.error("Wallet not connected");
            return;
        }

        const toastId = toast.loading("Processing transaction...");

        try {
            // Deserialize transaction
            const swapTransactionBuf = Uint8Array.from(atob(details.swapTransaction), c => c.charCodeAt(0));
            const transaction = VersionedTransaction.deserialize(swapTransactionBuf);

            // Sign transaction
            const signedTransaction = await signTransaction(transaction);

            // Send to RPC
            const signature = await connection.sendRawTransaction(signedTransaction.serialize());

            toast.loading("Confirming transaction...", { id: toastId });

            await connection.confirmTransaction(signature, 'confirmed');

            toast.success("Transaction executed!", {
                id: toastId,
                description: `Signature: ${signature.slice(0, 8)}...`
            });

        } catch (error) {
            console.error("Transaction failed", error);
            toast.error("Transaction failed", {
                id: toastId,
                description: error instanceof Error ? error.message : "Unknown error"
            });
        }
    };

    // Collapsed state - Show circular floating button
    if (!isOpen) {
        return (
            <button
                onClick={onToggle}
                className="fixed right-6 bottom-6 z-50 h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-xl hover:bg-primary/90 transition-all duration-300 flex items-center justify-center hover:scale-110 group"
                aria-label="Open Schumacher"
            >
                <MessageCircle className="h-6 w-6 group-hover:scale-110 transition-transform" />
                <span className="absolute -top-1 -right-1 h-4 w-4 bg-emerald-500 rounded-full border-2 border-background animate-pulse" />
            </button>
        );
    }

    // Expanded state - Show overlay chat panel
    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
                onClick={onToggle}
            />

            {/* Chat Panel */}
            <aside className="fixed right-4 bottom-4 top-4 w-[400px] z-50 flex flex-col animate-in slide-in-from-right duration-300">
                <div className="h-full flex flex-col bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
                    {/* Header */}
                    <div className="p-4 border-b border-border flex items-center justify-between bg-card">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-primary/10 rounded-lg">
                                <Sparkles className="h-5 w-5 text-primary" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-foreground">Schumacher</h3>
                                <p className="text-xs text-muted-foreground">AI Financial Advisor</p>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={onToggle}
                            className="text-muted-foreground hover:text-foreground"
                        >
                            <X className="h-5 w-5" />
                        </Button>
                    </div>

                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted/30">
                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={cn(
                                    "flex gap-3",
                                    msg.role === 'user' ? "flex-row-reverse" : ""
                                )}
                            >
                                {msg.role === 'assistant' && (
                                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                        <Sparkles className="h-4 w-4 text-primary" />
                                    </div>
                                )}

                                <div className={cn(
                                    "p-3 rounded-2xl shadow-sm max-w-[85%] text-sm",
                                    msg.role === 'user'
                                        ? "bg-primary text-primary-foreground rounded-tr-none"
                                        : "bg-card border border-border text-foreground rounded-tl-none"
                                )}>
                                    {msg.content}
                                    {msg.transactionDetails && (
                                        <div className="mt-3">
                                            <TransactionPreview
                                                details={msg.transactionDetails}
                                                onApprove={() => handleApprove(msg.transactionDetails!)}
                                                onReject={() => toast.info("Transaction rejected")}
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                    <Sparkles className="h-4 w-4 text-primary" />
                                </div>
                                <div className="bg-card border border-border p-3 rounded-2xl rounded-tl-none shadow-sm">
                                    <div className="flex gap-1">
                                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-card border-t border-border">
                        <div className="relative">
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask Schumacher..."
                                className="w-full resize-none rounded-xl border border-input bg-background p-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all h-[80px] text-foreground placeholder:text-muted-foreground"
                                disabled={isLoading}
                            />
                            <div className="absolute right-2 bottom-2 flex gap-1">
                                <Button
                                    size="icon"
                                    variant="ghost"
                                    className="h-8 w-8 rounded-lg text-muted-foreground hover:text-foreground transition-all"
                                    onClick={() => console.log("Voice input clicked")}
                                    title="Voice Input (Coming Soon)"
                                >
                                    <Mic className="h-4 w-4" />
                                </Button>
                                <Button
                                    size="icon"
                                    className="h-8 w-8 rounded-lg bg-primary hover:bg-primary/90 transition-all shadow-sm"
                                    onClick={handleSend}
                                    disabled={isLoading || !input.trim()}
                                >
                                    <Send className="h-4 w-4 text-primary-foreground" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
}
