import { apiClient } from './api-client';
import type { Goal, GoalFormData, PaginatedResponse } from '@/types';

class GoalsService {
  private readonly BASE_URL = '/api/v1/personal-planning/goals/';

  async getAll(): Promise<Goal[]> {
    const response = await apiClient.get<PaginatedResponse<Goal>>(this.BASE_URL);
    return response.results;
  }

  async getById(id: number): Promise<Goal> {
    return apiClient.get<Goal>(`${this.BASE_URL}${id}/`);
  }

  async create(data: GoalFormData): Promise<Goal> {
    return apiClient.post<Goal>(this.BASE_URL, data);
  }

  async update(id: number, data: Partial<GoalFormData>): Promise<Goal> {
    return apiClient.put<Goal>(`${this.BASE_URL}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${this.BASE_URL}${id}/`);
  }
}

export const goalsService = new GoalsService();
