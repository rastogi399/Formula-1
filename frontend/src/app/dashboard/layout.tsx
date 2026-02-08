import React from "react";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { DashboardThemeProvider } from "@/components/providers/DashboardThemeProvider";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <DashboardThemeProvider>
            <DashboardShell>{children}</DashboardShell>
        </DashboardThemeProvider>
    );
}
