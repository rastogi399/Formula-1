import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(value)
}

export function formatNumber(value: number): string {
    return new Intl.NumberFormat('en-US').format(value)
}

export function truncateAddress(address: string, length = 4): string {
    if (!address) return ''
    return `${address.slice(0, length)}...${address.slice(-length)}`
}

export function formatDate(date: string | Date): string {
    return new Date(date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    })
}

export function formatTime(date: string | Date): string {
    return new Date(date).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
    })
}
