"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

type Theme = "light" | "dark" | "system";

interface DashboardThemeContextType {
    theme: Theme;
    resolvedTheme: "light" | "dark";
    setTheme: (theme: Theme) => void;
}

const DashboardThemeContext = createContext<DashboardThemeContextType | undefined>(undefined);

export function useDashboardTheme() {
    const context = useContext(DashboardThemeContext);
    if (!context) {
        throw new Error("useDashboardTheme must be used within DashboardThemeProvider");
    }
    return context;
}

interface DashboardThemeProviderProps {
    children: React.ReactNode;
}

export function DashboardThemeProvider({ children }: DashboardThemeProviderProps) {
    const [theme, setThemeState] = useState<Theme>("dark");
    const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("dark");
    const [mounted, setMounted] = useState(false);

    // Load theme from localStorage on mount
    useEffect(() => {
        const stored = localStorage.getItem("dashboard-theme") as Theme | null;
        if (stored) {
            setThemeState(stored);
        }
        setMounted(true);
    }, []);

    // Resolve system theme
    useEffect(() => {
        const resolveTheme = () => {
            if (theme === "system") {
                const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
                setResolvedTheme(systemDark ? "dark" : "light");
            } else {
                setResolvedTheme(theme);
            }
        };

        resolveTheme();

        // Listen for system theme changes
        const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
        const handler = () => {
            if (theme === "system") {
                setResolvedTheme(mediaQuery.matches ? "dark" : "light");
            }
        };

        mediaQuery.addEventListener("change", handler);
        return () => mediaQuery.removeEventListener("change", handler);
    }, [theme]);

    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme);
        localStorage.setItem("dashboard-theme", newTheme);
    };

    if (!mounted) {
        return null;
    }

    return (
        <DashboardThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
            {children}
        </DashboardThemeContext.Provider>
    );
}
