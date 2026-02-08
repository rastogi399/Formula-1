"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { NeoCard } from "@/components/ui/neo-card";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in child component tree and displays fallback UI.
 * Follows React best practices for error handling.
 */
export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("ErrorBoundary caught an error:", error, errorInfo);
    }

    private handleRetry = () => {
        this.setState({ hasError: false, error: null });
    };

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <NeoCard className="p-8 text-center">
                    <div className="flex flex-col items-center gap-4">
                        <div className="p-4 bg-red-100 dark:bg-red-500/20 rounded-full">
                            <AlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-foreground">
                                Something went wrong
                            </h3>
                            <p className="text-sm text-muted-foreground mt-1">
                                An unexpected error occurred while rendering this component.
                            </p>
                            {this.state.error && (
                                <p className="text-xs text-muted-foreground mt-2 font-mono bg-muted p-2 rounded">
                                    {this.state.error.message}
                                </p>
                            )}
                        </div>
                        <Button onClick={this.handleRetry} variant="outline">
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Try Again
                        </Button>
                    </div>
                </NeoCard>
            );
        }

        return this.props.children;
    }
}

/**
 * Wrapper hook for functional components to use error boundary
 */
export function withErrorBoundary<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    fallback?: ReactNode
) {
    return function WithErrorBoundary(props: P) {
        return (
            <ErrorBoundary fallback={fallback}>
                <WrappedComponent {...props} />
            </ErrorBoundary>
        );
    };
}
