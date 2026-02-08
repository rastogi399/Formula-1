import { api } from "./client";

export interface ChallengeResponse {
    message: string;
    nonce: string;
}

export interface LoginResponse {
    token: string;
    wallet: string;
    expires_at: string;
}

export interface User {
    id: string;
    wallet_address: string;
    created_at: string;
}

export const authApi = {
    requestChallenge: async (wallet: string): Promise<ChallengeResponse> => {
        const response = await api.post<ChallengeResponse>("/auth/request-challenge", {
            wallet,
        });
        return response.data;
    },

    verifySignature: async (
        wallet: string,
        message: string,
        signature: string
    ): Promise<LoginResponse> => {
        const response = await api.post<LoginResponse>("/auth/verify-signature", {
            wallet,
            message,
            signature,
        });
        return response.data;
    },

    getCurrentUser: async (): Promise<User> => {
        const response = await api.get<User>("/auth/me");
        return response.data;
    },

    logout: async (): Promise<void> => {
        await api.post("/auth/logout");
    },
};
