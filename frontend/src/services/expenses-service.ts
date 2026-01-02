import { apiClient } from './api-client';
import { API_CONFIG } from '@/config/constants';
import type { Expense, ExpenseFormData, PaginatedResponse } from '@/types';

class ExpensesService {
  async getAll(params?: Record<string, any>): Promise<Expense[]> {
    const response = await apiClient.get<PaginatedResponse<Expense>>(API_CONFIG.ENDPOINTS.EXPENSES, params);
    return response.results;
  }

  async getById(id: number): Promise<Expense> {
    return apiClient.get<Expense>(`${API_CONFIG.ENDPOINTS.EXPENSES}${id}/`);
  }

  async create(data: ExpenseFormData): Promise<Expense> {
    return apiClient.post<Expense>(API_CONFIG.ENDPOINTS.EXPENSES, data);
  }

  async update(id: number, data: Partial<ExpenseFormData>): Promise<Expense> {
    return apiClient.put<Expense>(`${API_CONFIG.ENDPOINTS.EXPENSES}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${API_CONFIG.ENDPOINTS.EXPENSES}${id}/`);
  }

  async bulkMarkPaid(expenseIds: number[]): Promise<void> {
    return apiClient.post(`${API_CONFIG.ENDPOINTS.EXPENSES}bulk-mark-paid/`, {
      expense_ids: expenseIds
    });
  }
}

export const expensesService = new ExpensesService();
