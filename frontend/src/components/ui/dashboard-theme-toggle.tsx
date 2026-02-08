"use client";

import * as React from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { useDashboardTheme } from "@/components/providers/DashboardThemeProvider";

import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function DashboardThemeToggle() {
    const { theme, setTheme, resolvedTheme } = useDashboardTheme();

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon" className="relative">
                    <Sun className={`h-[1.2rem] w-[1.2rem] transition-all ${resolvedTheme === 'dark' ? 'rotate-90 scale-0' : 'rotate-0 scale-100'}`} />
                    <Moon className={`absolute h-[1.2rem] w-[1.2rem] transition-all ${resolvedTheme === 'dark' ? 'rotate-0 scale-100' : 'rotate-90 scale-0'}`} />
                    <span className="sr-only">Toggle theme</span>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setTheme("light")} className="gap-2">
                    <Sun className="h-4 w-4" />
                    Light
                    {theme === "light" && <span className="ml-auto text-primary">✓</span>}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")} className="gap-2">
                    <Moon className="h-4 w-4" />
                    Dark
                    {theme === "dark" && <span className="ml-auto text-primary">✓</span>}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")} className="gap-2">
                    <Monitor className="h-4 w-4" />
                    System
                    {theme === "system" && <span className="ml-auto text-primary">✓</span>}
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
