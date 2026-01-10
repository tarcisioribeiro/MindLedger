/**
 * AI Chat Store
 *
 * Zustand store for managing conversational AI Assistant state.
 * Persists session and message history to localStorage.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AIVisualization {
  type: 'chart' | 'cards' | 'table' | 'text';
  data?: {
    type?: 'pie' | 'bar' | 'line';
    data: any[];
    config?: any;
  };
  cards?: Array<{
    title: string;
    value: string;
    variant?: 'default' | 'success' | 'warning' | 'danger';
  }>;
  columns?: Array<{ key: string; label: string }>;
  rows?: any[];
}

export interface AISource {
  module: string;
  type: string;
  score: number;
  metadata: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: AISource[];
  visualization?: AIVisualization;
  streaming?: boolean;
}

interface AIChatState {
  // State
  sessionId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;

  // Actions
  setSessionId: (id: string) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  appendToMessage: (id: string, text: string) => void;
  setStreaming: (streaming: boolean) => void;
  clearMessages: () => void;
  reset: () => void;
}

const initialState = {
  sessionId: null,
  messages: [],
  isStreaming: false,
};

export const useAIChatStore = create<AIChatState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setSessionId: (id: string) => {
        set({ sessionId: id });
      },

      addMessage: (message: ChatMessage) => {
        set((state) => ({
          messages: [...state.messages, message],
        }));
      },

      updateMessage: (id: string, updates: Partial<ChatMessage>) => {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, ...updates } : msg
          ),
        }));
      },

      appendToMessage: (id: string, text: string) => {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, content: msg.content + text } : msg
          ),
        }));
      },

      setStreaming: (streaming: boolean) => {
        set({ isStreaming: streaming });
      },

      clearMessages: () => {
        set({ messages: [], sessionId: null });
      },

      reset: () => {
        set(initialState);
      },
    }),
    {
      name: 'ai-chat-storage',
      partialize: (state) => ({
        sessionId: state.sessionId,
        messages: state.messages.map((msg) => ({
          ...msg,
          // Convert Date to string for storage
          timestamp: msg.timestamp.toISOString(),
        })),
      }),
      // Rehydrate dates from strings
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.messages = state.messages.map((msg) => ({
            ...msg,
            // Convert string back to Date
            timestamp: new Date((msg.timestamp as unknown) as string),
          }));
        }
      },
    }
  )
);
