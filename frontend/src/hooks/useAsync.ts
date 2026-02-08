import { useState, useCallback } from "react";

interface UseAsyncState<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
}

interface UseAsyncReturn<T> extends UseAsyncState<T> {
    execute: () => Promise<void>;
    reset: () => void;
}

/**
 * Custom hook for async data fetching with loading and error states.
 * Promotes code reuse and consistent error handling across components.
 * 
 * @param asyncFn - The async function to execute
 * @param fallbackData - Optional fallback data to use when API fails
 * @returns Object with data, loading, error states and execute function
 * 
 * @example
 * ```tsx
 * const { data, loading, error, execute } = useAsync(
 *   () => api.fetchData(),
 *   fallbackData
 * );
 * 
 * useEffect(() => { execute(); }, []);
 * ```
 */
export function useAsync<T>(
    asyncFn: () => Promise<T>,
    fallbackData?: T
): UseAsyncReturn<T> {
    const [state, setState] = useState<UseAsyncState<T>>({
        data: null,
        loading: false,
        error: null,
    });

    const execute = useCallback(async () => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const result = await asyncFn();
            setState({ data: result, loading: false, error: null });
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "An error occurred";
            console.error("useAsync error:", err);

            setState({
                data: fallbackData ?? null,
                loading: false,
                error: errorMessage,
            });
        }
    }, [asyncFn, fallbackData]);

    const reset = useCallback(() => {
        setState({ data: null, loading: false, error: null });
    }, []);

    return {
        ...state,
        execute,
        reset,
    };
}

/**
 * Hook for toggling boolean state with single function.
 * Useful for modals, dropdowns, and other toggle UI elements.
 */
export function useToggle(initialValue = false): [boolean, () => void, (value: boolean) => void] {
    const [value, setValue] = useState(initialValue);

    const toggle = useCallback(() => setValue(prev => !prev), []);
    const set = useCallback((newValue: boolean) => setValue(newValue), []);

    return [value, toggle, set];
}

/**
 * Hook for managing form state with validation.
 * Simplifies form handling across the application.
 */
export function useFormField<T>(
    initialValue: T,
    validator?: (value: T) => string | null
): {
    value: T;
    error: string | null;
    onChange: (value: T) => void;
    validate: () => boolean;
    reset: () => void;
} {
    const [value, setValue] = useState<T>(initialValue);
    const [error, setError] = useState<string | null>(null);

    const onChange = useCallback((newValue: T) => {
        setValue(newValue);
        if (error) {
            setError(null);
        }
    }, [error]);

    const validate = useCallback(() => {
        if (validator) {
            const validationError = validator(value);
            setError(validationError);
            return validationError === null;
        }
        return true;
    }, [value, validator]);

    const reset = useCallback(() => {
        setValue(initialValue);
        setError(null);
    }, [initialValue]);

    return { value, error, onChange, validate, reset };
}

/**
 * Hook for debouncing a value.
 * Useful for search inputs and other frequently changing values.
 */
export function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useState(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(timer);
    });

    return debouncedValue;
}
