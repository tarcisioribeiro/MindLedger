import { apiClient } from './api-client';
import type {
  DailyTaskRecord,
  DailyTaskRecordFormData,
  TasksForTodayResponse,
  PaginatedResponse
} from '@/types';

class DailyTaskRecordsService {
  private readonly BASE_URL = '/api/v1/personal-planning/daily-records/';
  private readonly TASKS_TODAY_URL = '/api/v1/personal-planning/tasks-today/';

  async getAll(): Promise<DailyTaskRecord[]> {
    const response = await apiClient.get<PaginatedResponse<DailyTaskRecord>>(this.BASE_URL);
    return response.results;
  }

  async getById(id: number): Promise<DailyTaskRecord> {
    return apiClient.get<DailyTaskRecord>(`${this.BASE_URL}${id}/`);
  }

  async create(data: DailyTaskRecordFormData): Promise<DailyTaskRecord> {
    return apiClient.post<DailyTaskRecord>(this.BASE_URL, data);
  }

  async update(id: number, data: Partial<DailyTaskRecordFormData>): Promise<DailyTaskRecord> {
    return apiClient.put<DailyTaskRecord>(`${this.BASE_URL}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${this.BASE_URL}${id}/`);
  }

  async getTasksForToday(date?: string): Promise<TasksForTodayResponse> {
    const url = date ? `${this.TASKS_TODAY_URL}?date=${date}` : this.TASKS_TODAY_URL;
    return apiClient.get<TasksForTodayResponse>(url);
  }
}

export const dailyTaskRecordsService = new DailyTaskRecordsService();
