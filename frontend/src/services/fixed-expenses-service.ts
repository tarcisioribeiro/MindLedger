import { apiClient } from './api-client';
import { API_CONFIG } from '@/config/constants';
import type {
  FixedExpense,
  FixedExpenseFormData,
  BulkGenerateRequest,
  BulkGenerateResponse,
  FixedExpenseStats,
  PaginatedResponse
} from '@/types';

class FixedExpensesService {
  private baseUrl = API_CONFIG.ENDPOINTS.FIXED_EXPENSES;

  async getAll(params?: Record<string, any>): Promise<FixedExpense[]> {
    const response = await apiClient.get<PaginatedResponse<FixedExpense>>(
      this.baseUrl,
      params
    );
    return response.results;
  }

  async getById(id: number): Promise<FixedExpense> {
    return apiClient.get<FixedExpense>(`${this.baseUrl}${id}/`);
  }

  async create(data: FixedExpenseFormData): Promise<FixedExpense> {
    return apiClient.post<FixedExpense>(this.baseUrl, data);
  }

  async update(id: number, data: Partial<FixedExpenseFormData>): Promise<FixedExpense> {
    return apiClient.put<FixedExpense>(`${this.baseUrl}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${this.baseUrl}${id}/`);
  }

  async bulkGenerate(request: BulkGenerateRequest): Promise<BulkGenerateResponse> {
    return apiClient.post<BulkGenerateResponse>(
      `${this.baseUrl}generate/`,
      request
    );
  }

  async getStats(): Promise<FixedExpenseStats> {
    return apiClient.get<FixedExpenseStats>(`${this.baseUrl}stats/`);
  }
}

export const fixedExpensesService = new FixedExpensesService();
