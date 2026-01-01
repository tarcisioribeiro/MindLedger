import { apiClient } from './api-client';
import type { RoutineTask, RoutineTaskFormData, PaginatedResponse } from '@/types';

class RoutineTasksService {
  private readonly BASE_URL = '/api/v1/personal-planning/routine-tasks/';

  async getAll(): Promise<RoutineTask[]> {
    const response = await apiClient.get<PaginatedResponse<RoutineTask>>(this.BASE_URL);
    return response.results;
  }

  async getById(id: number): Promise<RoutineTask> {
    return apiClient.get<RoutineTask>(`${this.BASE_URL}${id}/`);
  }

  async create(data: RoutineTaskFormData): Promise<RoutineTask> {
    return apiClient.post<RoutineTask>(this.BASE_URL, data);
  }

  async update(id: number, data: Partial<RoutineTaskFormData>): Promise<RoutineTask> {
    return apiClient.put<RoutineTask>(`${this.BASE_URL}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${this.BASE_URL}${id}/`);
  }
}

export const routineTasksService = new RoutineTasksService();
