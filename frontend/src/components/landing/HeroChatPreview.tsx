"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight } from "lucide-react";

const MESSAGES = [
    { role: "user", text: "Set up a $100 weekly DCA from USDC to SOL" },
    { role: "ai", text: "I'll execute a 100 USDC → SOL swap every Monday at 00:00 UTC.", action: "View vault link" },
];

const TYPING_SPEED = 40;
const MESSAGE_DELAY = 1200;
const CURSOR_BLINK_SPEED = 530;

export default function HeroChatPreview() {
    const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
    const [displayedText, setDisplayedText] = useState("");
    const [isTyping, setIsTyping] = useState(true);
    const [showCursor, setShowCursor] = useState(true);
    const [visibleMessages, setVisibleMessages] = useState<any[]>([]);

    // Cursor blink effect
    useEffect(() => {
        const cursorInterval = setInterval(() => {
            setShowCursor((prev) => !prev);
        }, CURSOR_BLINK_SPEED);
        return () => clearInterval(cursorInterval);
    }, []);

    // Typing animation
    useEffect(() => {
        const currentMessage = MESSAGES[currentMessageIndex];
        if (!currentMessage) return;

        if (displayedText.length < currentMessage.text.length) {
            const timeout = setTimeout(() => {
                setDisplayedText(currentMessage.text.slice(0, displayedText.length + 1));
            }, TYPING_SPEED);
            return () => clearTimeout(timeout);
        } else {
            setIsTyping(false);
            const timeout = setTimeout(() => {
                // Add completed message to visible messages
                setVisibleMessages((prev) => {
                    const updated = [...prev, { ...currentMessage, id: Date.now() }];
                    // Keep only last 3 messages visible
                    return updated.slice(-3);
                });

                // Move to next message
                const nextIndex = (currentMessageIndex + 1) % MESSAGES.length;

                // Reset if looping back
                if (nextIndex === 0) {
                    setVisibleMessages([]);
                }

                setCurrentMessageIndex(nextIndex);
                setDisplayedText("");
                setIsTyping(true);
            }, MESSAGE_DELAY);
            return () => clearTimeout(timeout);
        }
    }, [displayedText, currentMessageIndex]);

    const currentMessage = MESSAGES[currentMessageIndex];

    return (
        <motion.div
            className="relative w-full max-w-md mx-auto"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
        >
            {/* Chat container - Neo-Brutalist Style */}
            <div className="relative z-10 border-4 border-black bg-white p-5 shadow-[8px_8px_0px_#000000]">
                {/* Header */}
                <div className="flex items-center gap-3 mb-6 pb-3 border-b-4 border-black">
                    <div className="relative">
                        <div className="w-10 h-10 bg-primary flex items-center justify-center border-2 border-black">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-secondary border-2 border-black" />
                    </div>
                    <div>
                        <p className="text-black font-bold text-lg leading-none">Schumacher</p>
                        <p className="text-gray-500 text-xs font-bold uppercase tracking-wider mt-1">Online • AI Agent</p>
                    </div>
                </div>

                {/* Messages container */}
                <div className="space-y-4 min-h-[200px]">
                    <AnimatePresence mode="popLayout">
                        {/* Previously completed messages */}
                        {visibleMessages.map((msg) => (
                            <motion.div
                                key={msg.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.3 }}
                                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div className="flex flex-col items-start gap-2 max-w-[90%]">
                                    <div
                                        className={`px-4 py-3 text-sm font-medium border-2 border-black shadow-[4px_4px_0px_#000000] ${msg.role === "user"
                                            ? "bg-primary text-white"
                                            : "bg-white text-black"
                                            }`}
                                    >
                                        {msg.text}
                                    </div>
                                    {msg.action && (
                                        <motion.button
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            className="px-3 py-1 bg-secondary text-black text-xs font-bold border-2 border-black shadow-[2px_2px_0px_#000000] hover:translate-y-[-2px] hover:shadow-[4px_4px_0px_#000000] transition-all flex items-center gap-1"
                                        >
                                            {msg.action} <ArrowRight className="w-3 h-3" />
                                        </motion.button>
                                    )}
                                </div>
                            </motion.div>
                        ))}

                        {/* Currently typing message */}
                        {currentMessage && (
                            <motion.div
                                key={`typing-${currentMessageIndex}`}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.2 }}
                                className={`flex ${currentMessage.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div
                                    className={`max-w-[90%] px-4 py-3 text-sm font-medium border-2 border-black shadow-[4px_4px_0px_#000000] ${currentMessage.role === "user"
                                        ? "bg-primary text-white"
                                        : "bg-white text-black"
                                        }`}
                                >
                                    <span>{displayedText}</span>
                                    <span
                                        className={`inline-block w-2 h-4 ml-1 align-middle ${currentMessage.role === "user" ? "bg-white" : "bg-black"
                                            } ${showCursor && isTyping ? "opacity-100" : "opacity-0"}`}
                                    />
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Input area mock */}
                <div className="mt-6 pt-4 border-t-4 border-black">
                    <div className="flex items-center gap-2 px-3 py-3 bg-white border-2 border-black shadow-[4px_4px_0px_#000000]">
                        <input
                            type="text"
                            placeholder="Type a command..."
                            disabled
                            className="flex-1 bg-transparent text-sm text-black placeholder:text-gray-400 font-medium outline-none cursor-not-allowed"
                        />
                        <button
                            disabled
                            className="p-2 bg-primary text-white border-2 border-black opacity-100 cursor-not-allowed hover:bg-primary/90"
                        >
                            <ArrowRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
