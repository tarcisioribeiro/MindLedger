/**
 * Service para comunicação com o AI Assistant.
 */
import { apiClient } from './api-client';
import type { AiResponse, AiHealthResponse, AiHistoryResponse } from '@/types';

class AiAssistantService {
  private readonly baseUrl = '/api/v1/ai';

  /**
   * Envia uma pergunta para o assistente de IA.
   */
  async pergunta(pergunta: string): Promise<AiResponse> {
    return apiClient.post<AiResponse>(`${this.baseUrl}/pergunta/`, {
      pergunta,
    });
  }

  /**
   * Obtém o histórico de conversas.
   */
  async getHistorico(limit: number = 20): Promise<AiHistoryResponse> {
    return apiClient.get<AiHistoryResponse>(
      `${this.baseUrl}/historico/?limit=${limit}`
    );
  }

  /**
   * Verifica a saúde do serviço de IA.
   */
  async checkHealth(): Promise<AiHealthResponse> {
    return apiClient.get<AiHealthResponse>(`${this.baseUrl}/health/`);
  }
}

export const aiAssistantService = new AiAssistantService();
