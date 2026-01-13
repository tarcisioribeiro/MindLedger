import { apiClient } from './api-client';
import type { DashboardStats, AccountBalance } from '@/types';

class DashboardService {
  async getStats(): Promise<DashboardStats> {
    // PERF-02: Endpoint otimizado que usa aggregations no banco de dados
    // Reduz de 4 requisições + cálculos no cliente para 1 requisição otimizada
    return apiClient.get<DashboardStats>('/api/v1/dashboard/stats/');
  }

  async getAccountBalances(): Promise<AccountBalance[]> {
    return apiClient.get<AccountBalance[]>('/api/v1/dashboard/account-balances/');
  }
}

export const dashboardService = new DashboardService();
