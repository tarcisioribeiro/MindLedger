import { apiClient } from './api-client';
import type {
  TaskInstance,
  TaskInstanceFormData,
  TaskInstanceUpdateData,
  InstancesForDateResponse,
  TaskInstanceBulkUpdate,
  TaskInstanceBulkUpdateResponse,
  InstanceStatus,
} from '@/types';

const BASE_URL = '/api/v1/personal-planning/instances/';

class TaskInstancesService {
  /**
   * Lista todas as instâncias de tarefas.
   * Suporta filtros por date, status e template.
   */
  async getAll(params?: {
    date?: string;
    status?: InstanceStatus;
    template?: number;
  }): Promise<TaskInstance[]> {
    const queryParams = new URLSearchParams();
    if (params?.date) queryParams.append('date', params.date);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.template) queryParams.append('template', params.template.toString());

    const url = queryParams.toString() ? `${BASE_URL}?${queryParams}` : BASE_URL;
    const response = await apiClient.get<{ results: TaskInstance[] } | TaskInstance[]>(url);

    // Handle both paginated and non-paginated responses
    return Array.isArray(response) ? response : response.results;
  }

  /**
   * Obtém uma instância específica por ID.
   */
  async getById(id: number): Promise<TaskInstance> {
    return apiClient.get<TaskInstance>(`${BASE_URL}${id}/`);
  }

  /**
   * Cria uma nova tarefa avulsa (one-off task).
   */
  async create(data: TaskInstanceFormData): Promise<TaskInstance> {
    return apiClient.post<TaskInstance>(BASE_URL, data);
  }

  /**
   * Atualiza uma instância existente.
   */
  async update(id: number, data: TaskInstanceUpdateData): Promise<TaskInstance> {
    return apiClient.patch<TaskInstance>(`${BASE_URL}${id}/`, data);
  }

  /**
   * Atualiza apenas o status de uma instância.
   */
  async updateStatus(id: number, status: InstanceStatus, notes?: string): Promise<TaskInstance> {
    return apiClient.patch<TaskInstance>(`${BASE_URL}${id}/status/`, { status, notes });
  }

  /**
   * Deleta uma instância (soft delete).
   */
  async delete(id: number): Promise<void> {
    return apiClient.delete(`${BASE_URL}${id}/`);
  }

  /**
   * Obtém ou gera instâncias para uma data específica.
   * Este é o principal método para carregar o Kanban/checklist diário.
   */
  async getForDate(date: string): Promise<InstancesForDateResponse> {
    return apiClient.get<InstancesForDateResponse>(`${BASE_URL}for-date/?date=${date}`);
  }

  /**
   * Atualiza múltiplas instâncias de uma vez.
   * Útil para salvar o estado do Kanban.
   */
  async bulkUpdate(updates: TaskInstanceBulkUpdate[]): Promise<TaskInstanceBulkUpdateResponse> {
    return apiClient.post<TaskInstanceBulkUpdateResponse>(`${BASE_URL}bulk-update/`, { updates });
  }

  /**
   * Helper: Formata a data atual no formato YYYY-MM-DD.
   */
  getTodayDate(): string {
    return new Date().toISOString().split('T')[0];
  }

  /**
   * Helper: Obtém instâncias do dia atual.
   */
  async getForToday(): Promise<InstancesForDateResponse> {
    return this.getForDate(this.getTodayDate());
  }
}

export const taskInstancesService = new TaskInstancesService();
