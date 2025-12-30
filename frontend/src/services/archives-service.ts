import { apiClient } from './api-client';
import { API_CONFIG } from '@/config/constants';
import type { Archive, ArchiveFormData, ArchiveReveal, PaginatedResponse } from '@/types';

class ArchivesService {
  async getAll(): Promise<Archive[]> {
    const response = await apiClient.get<PaginatedResponse<Archive>>(API_CONFIG.ENDPOINTS.ARCHIVES);
    return response.results;
  }

  async getById(id: number): Promise<Archive> {
    return apiClient.get<Archive>(`${API_CONFIG.ENDPOINTS.ARCHIVES}${id}/`);
  }

  async create(data: ArchiveFormData): Promise<Archive> {
    return apiClient.post<Archive>(API_CONFIG.ENDPOINTS.ARCHIVES, data);
  }

  async update(id: number, data: Partial<ArchiveFormData>): Promise<Archive> {
    return apiClient.put<Archive>(`${API_CONFIG.ENDPOINTS.ARCHIVES}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${API_CONFIG.ENDPOINTS.ARCHIVES}${id}/`);
  }

  async reveal(id: number): Promise<ArchiveReveal> {
    return apiClient.get<ArchiveReveal>(`${API_CONFIG.ENDPOINTS.ARCHIVES}${id}/reveal/`);
  }

  async download(id: number): Promise<Blob> {
    const response = await apiClient.get(`${API_CONFIG.ENDPOINTS.ARCHIVES}${id}/download/`, {
      responseType: 'blob',
    });
    return response as unknown as Blob;
  }
}

export const archivesService = new ArchivesService();
