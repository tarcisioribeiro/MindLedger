/**
 * Service para comunicação com o AI Assistant.
 *
 * Suporta agentes especializados com modelos e escopos diferentes.
 */
import { apiClient } from './api-client';
import type {
  AiResponse,
  AiHealthResponse,
  AiHistoryResponse,
  AiAgentsResponse,
} from '@/types';

class AiAssistantService {
  private readonly baseUrl = '/api/v1/ai';

  /**
   * Envia uma pergunta para um agente especializado.
   *
   * @param pergunta - A pergunta em linguagem natural
   * @param agent - O key do agente a ser usado (ex: 'financial', 'security')
   */
  async pergunta(pergunta: string, agent: string): Promise<AiResponse> {
    return apiClient.post<AiResponse>(`${this.baseUrl}/pergunta/`, {
      pergunta,
      agent,
    });
  }

  /**
   * Obtém a lista de agentes disponíveis.
   */
  async getAgents(): Promise<AiAgentsResponse> {
    return apiClient.get<AiAgentsResponse>(`${this.baseUrl}/agents/`);
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
