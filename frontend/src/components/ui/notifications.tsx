"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

type NotificationType = "success" | "error" | "warning" | "info";

interface Notification {
    id: string;
    type: NotificationType;
    title: string;
    message?: string;
    duration?: number;
    action?: {
        label: string;
        onClick: () => void;
    };
}

interface NotificationContextType {
    notifications: Notification[];
    addNotification: (notification: Omit<Notification, "id">) => string;
    removeNotification: (id: string) => void;
    clearAll: () => void;
    // Convenience methods
    success: (title: string, message?: string) => string;
    error: (title: string, message?: string) => string;
    warning: (title: string, message?: string) => string;
    info: (title: string, message?: string) => string;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

const DEFAULT_DURATION = 5000;

/**
 * Generate unique ID for notifications
 */
function generateId(): string {
    return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Notification Provider Component
 * Wraps the application to provide notification functionality
 */
export function NotificationProvider({ children }: { children: ReactNode }) {
    const [notifications, setNotifications] = useState<Notification[]>([]);

    const removeNotification = useCallback((id: string) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    const addNotification = useCallback((notification: Omit<Notification, "id">) => {
        const id = generateId();
        const newNotification: Notification = {
            ...notification,
            id,
            duration: notification.duration ?? DEFAULT_DURATION,
        };

        setNotifications(prev => [...prev, newNotification]);

        // Auto-remove after duration
        if (newNotification.duration && newNotification.duration > 0) {
            setTimeout(() => removeNotification(id), newNotification.duration);
        }

        return id;
    }, [removeNotification]);

    const clearAll = useCallback(() => {
        setNotifications([]);
    }, []);

    // Convenience methods
    const success = useCallback((title: string, message?: string) => {
        return addNotification({ type: "success", title, message });
    }, [addNotification]);

    const error = useCallback((title: string, message?: string) => {
        return addNotification({ type: "error", title, message, duration: 8000 });
    }, [addNotification]);

    const warning = useCallback((title: string, message?: string) => {
        return addNotification({ type: "warning", title, message });
    }, [addNotification]);

    const info = useCallback((title: string, message?: string) => {
        return addNotification({ type: "info", title, message });
    }, [addNotification]);

    return (
        <NotificationContext.Provider
            value={{
                notifications,
                addNotification,
                removeNotification,
                clearAll,
                success,
                error,
                warning,
                info,
            }}
        >
            {children}
            <NotificationContainer
                notifications={notifications}
                onDismiss={removeNotification}
            />
        </NotificationContext.Provider>
    );
}

/**
 * Hook to use notifications
 */
export function useNotifications() {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error("useNotifications must be used within a NotificationProvider");
    }
    return context;
}

/**
 * Notification Container - Renders all active notifications
 */
function NotificationContainer({
    notifications,
    onDismiss,
}: {
    notifications: Notification[];
    onDismiss: (id: string) => void;
}) {
    if (notifications.length === 0) return null;

    return (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
            {notifications.map((notification) => (
                <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onDismiss={() => onDismiss(notification.id)}
                />
            ))}
        </div>
    );
}

/**
 * Individual Notification Item
 */
function NotificationItem({
    notification,
    onDismiss,
}: {
    notification: Notification;
    onDismiss: () => void;
}) {
    const icons = {
        success: CheckCircle,
        error: XCircle,
        warning: AlertTriangle,
        info: Info,
    };

    const colors = {
        success: {
            bg: "bg-emerald-50 dark:bg-emerald-500/10",
            border: "border-emerald-200 dark:border-emerald-500/20",
            icon: "text-emerald-600 dark:text-emerald-400",
        },
        error: {
            bg: "bg-red-50 dark:bg-red-500/10",
            border: "border-red-200 dark:border-red-500/20",
            icon: "text-red-600 dark:text-red-400",
        },
        warning: {
            bg: "bg-amber-50 dark:bg-amber-500/10",
            border: "border-amber-200 dark:border-amber-500/20",
            icon: "text-amber-600 dark:text-amber-400",
        },
        info: {
            bg: "bg-blue-50 dark:bg-blue-500/10",
            border: "border-blue-200 dark:border-blue-500/20",
            icon: "text-blue-600 dark:text-blue-400",
        },
    };

    const Icon = icons[notification.type];
    const color = colors[notification.type];

    return (
        <div
            className={cn(
                "flex items-start gap-3 p-4 rounded-xl border shadow-lg",
                "animate-in slide-in-from-right-5 fade-in duration-200",
                color.bg,
                color.border
            )}
            role="alert"
        >
            <Icon className={cn("h-5 w-5 flex-shrink-0 mt-0.5", color.icon)} />

            <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground text-sm">
                    {notification.title}
                </p>
                {notification.message && (
                    <p className="text-xs text-muted-foreground mt-0.5">
                        {notification.message}
                    </p>
                )}
                {notification.action && (
                    <button
                        onClick={notification.action.onClick}
                        className="text-xs font-medium text-primary hover:underline mt-2"
                    >
                        {notification.action.label}
                    </button>
                )}
            </div>

            <button
                onClick={onDismiss}
                className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                aria-label="Dismiss notification"
            >
                <X className="h-4 w-4 text-muted-foreground" />
            </button>
        </div>
    );
}

/**
 * DCA Execution Notification Helper
 * Use this to notify users about DCA automation events
 */
export function notifyDCAExecution(
    notifications: NotificationContextType,
    event: {
        type: "executed" | "failed" | "paused" | "resumed" | "completed";
        automationName: string;
        amount?: number;
        token?: string;
        error?: string;
    }
) {
    switch (event.type) {
        case "executed":
            notifications.success(
                "DCA Executed",
                `${event.automationName}: Swapped ${event.amount} ${event.token}`
            );
            break;
        case "failed":
            notifications.error(
                "DCA Execution Failed",
                `${event.automationName}: ${event.error || "Unknown error"}`
            );
            break;
        case "paused":
            notifications.warning(
                "Automation Paused",
                `${event.automationName} has been paused`
            );
            break;
        case "resumed":
            notifications.info(
                "Automation Resumed",
                `${event.automationName} is now active`
            );
            break;
        case "completed":
            notifications.success(
                "Automation Completed",
                `${event.automationName} has finished all cycles`
            );
            break;
    }
}
