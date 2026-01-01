import { apiClient } from './api-client';
import type { DailyReflection, DailyReflectionFormData, PaginatedResponse } from '@/types';

class DailyReflectionsService {
  private readonly BASE_URL = '/api/v1/personal-planning/reflections/';

  async getAll(): Promise<DailyReflection[]> {
    const response = await apiClient.get<PaginatedResponse<DailyReflection>>(this.BASE_URL);
    return response.results;
  }

  async getById(id: number): Promise<DailyReflection> {
    return apiClient.get<DailyReflection>(`${this.BASE_URL}${id}/`);
  }

  async create(data: DailyReflectionFormData): Promise<DailyReflection> {
    return apiClient.post<DailyReflection>(this.BASE_URL, data);
  }

  async update(id: number, data: Partial<DailyReflectionFormData>): Promise<DailyReflection> {
    return apiClient.put<DailyReflection>(`${this.BASE_URL}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${this.BASE_URL}${id}/`);
  }
}

export const dailyReflectionsService = new DailyReflectionsService();
