/**
 * AI Streaming Service
 *
 * Client for Server-Sent Events (SSE) streaming with the AI Assistant.
 * Handles real-time streaming of AI responses with visualization data.
 */

import { API_CONFIG } from '@/config/constants';

export interface StreamEvent {
  event:
    | 'intent'
    | 'message_start'
    | 'content_chunk'
    | 'visualization'
    | 'sources'
    | 'message_end'
    | 'error';
  data: any;
}

export type StreamCallback = (event: StreamEvent) => void;

class AIStreamingService {
  private abortController: AbortController | null = null;

  /**
   * Stream a query to the AI Assistant with Server-Sent Events.
   *
   * @param question - User's question
   * @param sessionId - Optional session ID for conversation continuity
   * @param onEvent - Callback for each SSE event
   * @param topK - Number of results to retrieve (default: 10)
   * @returns Promise that resolves with the session ID
   */
  async streamQuery(
    question: string,
    sessionId: string | null,
    onEvent: StreamCallback,
    topK: number = 10
  ): Promise<string> {
    // Close existing connection
    this.closeStream();

    // Create new abort controller
    this.abortController = new AbortController();

    return new Promise((resolve, reject) => {
      fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.AI_STREAM}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          session_id: sessionId,
          top_k: topK,
        }),
        credentials: 'include', // Important: send httpOnly cookies
        signal: this.abortController.signal,
      })
        .then(async (response) => {
          if (!response.ok) {
            const error = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(error.error || `HTTP error! status: ${response.status}`);
          }

          // Get session ID from header
          const newSessionId = response.headers.get('Session-ID');

          // Read stream
          const reader = response.body!.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          const processStream = async () => {
            try {
              while (true) {
                const { done, value } = await reader.read();

                if (done) {
                  resolve(newSessionId || sessionId || '');
                  break;
                }

                // Decode chunk
                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE messages
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || ''; // Keep incomplete message in buffer

                for (const line of lines) {
                  if (line.trim()) {
                    const event = this.parseSSE(line);
                    if (event) {
                      onEvent(event);
                    }
                  }
                }
              }
            } catch (error: any) {
              if (error.name === 'AbortError') {
                console.log('Stream aborted by user');
                resolve(newSessionId || sessionId || '');
              } else {
                reject(error);
              }
            }
          };

          processStream();
        })
        .catch((error) => {
          if (error.name === 'AbortError') {
            console.log('Request aborted');
            resolve(sessionId || '');
          } else {
            reject(error);
          }
        });
    });
  }

  /**
   * Parse a Server-Sent Event message.
   *
   * @param message - Raw SSE message
   * @returns Parsed StreamEvent or null
   */
  private parseSSE(message: string): StreamEvent | null {
    const lines = message.split('\n');
    let event = 'message';
    let data = '';

    for (const line of lines) {
      if (line.startsWith('event:')) {
        event = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        data = line.slice(5).trim();
      }
    }

    if (!data) return null;

    try {
      return {
        event: event as StreamEvent['event'],
        data: JSON.parse(data),
      };
    } catch {
      // If not JSON, treat as plain text
      return {
        event: event as StreamEvent['event'],
        data: { text: data },
      };
    }
  }

  /**
   * Close the current streaming connection.
   */
  closeStream() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}

// Export singleton instance
export const aiStreamingService = new AIStreamingService();
