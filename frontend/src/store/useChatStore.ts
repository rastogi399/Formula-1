import { create } from 'zustand';
import { chatApi } from '@/lib/api';

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
    transactionDetails?: import('@/components/chat/TransactionPreview').TransactionDetails;
}

interface ChatState {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
    sendMessage: (content: string) => Promise<void>;
    addMessage: (message: Message) => void;
    clearChat: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
    messages: [
        {
            id: 'welcome',
            role: 'assistant',
            content: "Hi! I'm your AI financial advisor. I can help you swap tokens, analyze risk, or set up DCA strategies. What's on your mind?",
            timestamp: Date.now(),
        }
    ],
    isLoading: false,
    error: null,

    addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
    })),

    sendMessage: async (content: string) => {
        const { messages, addMessage } = get();

        // Add user message immediately
        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content,
            timestamp: Date.now(),
        };
        addMessage(userMsg);

        set({ isLoading: true, error: null });

        try {
            // Prepare history for API (exclude welcome message if needed, or map to backend format)
            const history = messages.map(m => ({ role: m.role, content: m.content }));

            // Call API
            const response = await chatApi.sendMessage(content, history);

            // Add AI response
            const aiMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.message || "I processed your request.",
                timestamp: Date.now(),
                transactionDetails: response.transaction // Assuming backend returns this
            };
            addMessage(aiMsg);
        } catch (error) {
            console.error('Chat error:', error);
            set({ error: 'Failed to send message. Please try again.' });

            // Optional: Add error message to chat
            addMessage({
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "Sorry, I encountered an error. Please try again.",
                timestamp: Date.now(),
            });
        } finally {
            set({ isLoading: false });
        }
    },

    clearChat: () => set({ messages: [] }),
}));
