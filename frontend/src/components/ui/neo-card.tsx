import { cn } from "@/lib/utils";
import React from "react";

interface NeoCardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    className?: string;
    variant?: "default" | "highlight" | "dark";
}

export function NeoCard({ children, className, variant = "default", ...props }: NeoCardProps) {
    return (
        <div
            className={cn(
                "border-4 border-black transition-all duration-300",
                {
                    "bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[12px_12px_0px_0px_rgba(153,69,255,1)]": variant === "default",
                    "bg-primary/10 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:shadow-[12px_12px_0px_0px_rgba(32,128,160,1)]": variant === "highlight",
                    "bg-zinc-900 border-white/20 text-white shadow-[8px_8px_0px_0px_rgba(255,255,255,0.2)]": variant === "dark",
                },
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}
