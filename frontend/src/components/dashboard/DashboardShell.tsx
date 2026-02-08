"use client";

import React, { useState, useEffect } from "react";
import { DashboardNav } from "@/components/dashboard/DashboardNav";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { ChatWidget } from "../chat/ChatSidebar";
import { useDashboardTheme } from "@/components/providers/DashboardThemeProvider";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export function DashboardShell({ children }: { children: React.ReactNode }) {
    const { resolvedTheme } = useDashboardTheme();
    const [mounted, setMounted] = useState(false);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) return null;

    return (
        <div className={`min-h-screen bg-background relative overflow-x-hidden ${resolvedTheme === 'dark' ? 'dark' : ''}`}>
            {/* Background Aurora Effect */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-primary/5 blur-[100px] animate-pulse" />
                <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-secondary/5 blur-[80px]" />
            </div>

            {/* Mobile Header */}
            <div className="lg:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between p-4 bg-background/80 backdrop-blur-md border-b border-border">
                <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
                    <SheetTrigger asChild>
                        <Button variant="ghost" size="icon">
                            <Menu className="h-6 w-6" />
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="p-0 w-64 border-r border-border bg-card">
                        <DashboardNav />
                    </SheetContent>
                </Sheet>
                <DashboardHeader />
            </div>

            {/* Desktop Sidebar */}
            <div className="hidden lg:block">
                <DashboardNav />
            </div>

            {/* Main Content Area */}
            <main className="relative z-10 transition-all duration-300 ease-in-out min-h-screen lg:ml-64 flex flex-col pt-16 lg:pt-0">
                {/* Desktop Top Navbar */}
                <div className="hidden lg:block">
                    <DashboardHeader />
                </div>

                {/* Page Content */}
                <div className="flex-1 p-4 lg:p-8 max-w-7xl mx-auto w-full">
                    {children}
                </div>
            </main>

            {/* Right Chat Sidebar - Overlay, doesn't take space */}
            <ChatWidget isOpen={isChatOpen} onToggle={() => setIsChatOpen(!isChatOpen)} />
        </div>
    );
}
