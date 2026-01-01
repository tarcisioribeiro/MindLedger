import { apiClient } from './api-client';
import type { PersonalPlanningDashboardStats } from '@/types';

class PersonalPlanningDashboardService {
  async getStats(): Promise<PersonalPlanningDashboardStats> {
    return await apiClient.get<PersonalPlanningDashboardStats>(
      '/api/v1/personal-planning/dashboard/stats/'
    );
  }
}

export const personalPlanningDashboardService = new PersonalPlanningDashboardService();
