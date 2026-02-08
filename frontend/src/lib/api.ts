import axios from 'axios';

// Build API base URL robustly. If NEXT_PUBLIC_API_URL includes an /api path, use it as-is.
const rawEnv = process.env.NEXT_PUBLIC_API_URL;
let API_URL = rawEnv ? rawEnv.replace(/\/+$/, '') : '';
if (!API_URL) {
    API_URL = 'http://localhost:8000/api/v1';
} else if (!/\/api\//.test(API_URL)) {
    // If environment doesn't include an API route, append our default prefix
    API_URL = `${API_URL}/api/v1`;
}

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 15000,
});

// Add request interceptor to include auth token if available (only in browser)
api.interceptors.request.use((config) => {
    try {
        if (typeof window !== 'undefined' && window.localStorage) {
            const token = window.localStorage.getItem('token');
            if (token && config && config.headers) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
    } catch (e) {
        // swallow storage errors (e.g., blocked storage)
    }
    return config;
});

// Response interceptor to normalize network errors and provide clearer messages
api.interceptors.response.use(
    (res) => res,
    (error) => {
        // If no response, it's likely a network error / CORS / backend down
        if (!error.response) {
            const msg = `Network Error: unable to reach API at ${API_URL}`;
            const netErr: any = new Error(msg);
            netErr.original = error;
            return Promise.reject(netErr);
        }
        return Promise.reject(error);
    }
);

export const chatApi = {
    sendMessage: async (message: string, history: any[]) => {
        const response = await api.post('/chat/send', { message, history });
        return response.data;
    },
    getHistory: async () => {
        const response = await api.get('/chat/history');
        return response.data;
    },
};

export const authApi = {
    requestChallenge: async (wallet: string) => {
        const response = await api.post('/auth/request-challenge', { wallet });
        return response.data;
    },
    verifySignature: async (wallet: string, message: string, signature: string) => {
        const response = await api.post('/auth/verify-signature', { wallet, message, signature });
        return response.data;
    }
};

// Portfolio API
export const portfolioApi = {
    getPortfolio: async () => {
        const response = await api.get('/portfolio/');
        return response.data;
    },
    getHoldings: async () => {
        const response = await api.get('/portfolio/holdings');
        return response.data;
    },
    getPerformance: async (timeframe: string = '30d') => {
        const response = await api.get(`/portfolio/performance?timeframe=${timeframe}`);
        return response.data;
    },
    getHistory: async (timeframe: string = '30d') => {
        const response = await api.get(`/portfolio/history?timeframe=${timeframe}`);
        return response.data;
    },
    getRisk: async () => {
        const response = await api.get('/portfolio/risk');
        return response.data;
    },
    createSnapshot: async () => {
        const response = await api.post('/portfolio/snapshot');
        return response.data;
    }
};

// Automations API
export const automationsApi = {
    getAutomations: async (status?: string, type?: string) => {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (type) params.append('automation_type', type);
        const response = await api.get(`/automations/?${params.toString()}`);
        return response.data;
    },
    getAutomation: async (id: string) => {
        const response = await api.get(`/automations/${id}`);
        return response.data;
    },
    createAutomation: async (data: {
        automation_type: 'dca' | 'recurring_swap' | 'rebalance';
        name: string;
        source_token: string;
        dest_token: string;
        amount: number;
        frequency_seconds: number;
        metadata?: Record<string, unknown>;
    }) => {
        const response = await api.post('/automations/', data);
        return response.data;
    },
    pauseAutomation: async (id: string) => {
        const response = await api.post(`/automations/${id}/pause`);
        return response.data;
    },
    resumeAutomation: async (id: string) => {
        const response = await api.post(`/automations/${id}/resume`);
        return response.data;
    },
    deleteAutomation: async (id: string) => {
        const response = await api.delete(`/automations/${id}`);
        return response.data;
    },
    getExecutions: async (automationId: string, limit: number = 50) => {
        const response = await api.get(`/automations/${automationId}/executions?limit=${limit}`);
        return response.data;
    },
    // On-chain vault deployment methods
    getDeployInstruction: async (automationId: string) => {
        const response = await api.get(`/automations/${automationId}/deploy-instruction`);
        return response.data;
    },
    confirmDeployment: async (automationId: string, txHash: string) => {
        const response = await api.post(`/automations/${automationId}/confirm-deployment?tx_hash=${txHash}`);
        return response.data;
    },
};

// Transactions API
export const transactionsApi = {
    getTransactions: async (limit: number = 50, offset: number = 0, action?: string, status?: string) => {
        const params = new URLSearchParams();
        params.append('limit', limit.toString());
        params.append('offset', offset.toString());
        if (action) params.append('action', action);
        if (status) params.append('status', status);
        const response = await api.get(`/transactions/?${params.toString()}`);
        return response.data;
    },
    getTransaction: async (id: string) => {
        const response = await api.get(`/transactions/${id}`);
        return response.data;
    },
    getStats: async (timeframe: string = '30d') => {
        const response = await api.get(`/transactions/stats/summary?timeframe=${timeframe}`);
        return response.data;
    },
    getRecentActivity: async (limit: number = 10) => {
        const response = await api.get(`/transactions/recent/activity?limit=${limit}`);
        return response.data;
    }
};

// Session Keys API
export const sessionKeysApi = {
    getSessionKeys: async () => {
        const response = await api.get('/session-keys');
        return response.data;
    },
    createSessionKey: async (data: {
        name: string;
        max_amount_per_tx: number;
        max_total_amount: number;
        expires_in_days?: number;
        allowed_programs?: string[];
    }) => {
        const response = await api.post('/session-keys', data);
        return response.data;
    },
    getSessionKey: async (id: string) => {
        const response = await api.get(`/session-keys/${id}`);
        return response.data;
    },
    updateSessionKey: async (id: string, data: {
        max_amount_per_tx?: number;
        max_total_amount?: number;
    }) => {
        const response = await api.patch(`/session-keys/${id}`, data);
        return response.data;
    },
    revokeSessionKey: async (id: string) => {
        const response = await api.post(`/session-keys/${id}/revoke`);
        return response.data;
    },
    deleteSessionKey: async (id: string) => {
        const response = await api.delete(`/session-keys/${id}`);
        return response.data;
    },
    validateSessionKey: async (id: string, programId: string, amount: number) => {
        const response = await api.post(`/session-keys/${id}/validate?program_id=${programId}&amount=${amount}`);
        return response.data;
    }
};
