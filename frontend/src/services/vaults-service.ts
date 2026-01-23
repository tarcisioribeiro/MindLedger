import { apiClient } from './api-client';
import type {
  Vault,
  VaultFormData,
  VaultTransaction,
  VaultDepositData,
  VaultWithdrawData,
  VaultYieldUpdateData,
  VaultOperationResponse,
  VaultYieldResponse,
  VaultYieldUpdateResponse,
  VaultTransactionUpdateData,
  VaultTransactionUpdateResponse,
  VaultTransactionDeleteResponse,
  FinancialGoal,
  FinancialGoalListItem,
  FinancialGoalFormData,
  FinancialGoalCheckResponse,
  FinancialGoalVaultsRequest,
  FinancialGoalVaultsResponse,
  PaginatedResponse,
} from '@/types';

const VAULTS_BASE_URL = '/api/v1/vaults/';
const TRANSACTIONS_BASE_URL = '/api/v1/vault-transactions/';
const GOALS_BASE_URL = '/api/v1/financial-goals/';

class VaultsService {
  // ==================== VAULTS ====================

  async getAll(params?: { account?: number; is_active?: boolean }): Promise<Vault[]> {
    let url = VAULTS_BASE_URL;
    const searchParams = new URLSearchParams();

    if (params?.account) {
      searchParams.append('account', params.account.toString());
    }
    if (params?.is_active !== undefined) {
      searchParams.append('is_active', params.is_active.toString());
    }

    if (searchParams.toString()) {
      url += `?${searchParams.toString()}`;
    }

    const response = await apiClient.get<PaginatedResponse<Vault>>(url);
    return response.results;
  }

  async getById(id: number): Promise<Vault> {
    return apiClient.get<Vault>(`${VAULTS_BASE_URL}${id}/`);
  }

  async create(data: VaultFormData): Promise<Vault> {
    return apiClient.post<Vault>(VAULTS_BASE_URL, data);
  }

  async update(id: number, data: Partial<VaultFormData>): Promise<Vault> {
    return apiClient.put<Vault>(`${VAULTS_BASE_URL}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${VAULTS_BASE_URL}${id}/`);
  }

  // Vault Operations
  async deposit(id: number, data: VaultDepositData): Promise<VaultOperationResponse> {
    return apiClient.post<VaultOperationResponse>(`${VAULTS_BASE_URL}${id}/deposit/`, data);
  }

  async withdraw(id: number, data: VaultWithdrawData): Promise<VaultOperationResponse> {
    return apiClient.post<VaultOperationResponse>(`${VAULTS_BASE_URL}${id}/withdraw/`, data);
  }

  async applyYield(id: number): Promise<VaultYieldResponse> {
    return apiClient.post<VaultYieldResponse>(`${VAULTS_BASE_URL}${id}/apply-yield/`, {});
  }

  async updateYield(id: number, data: VaultYieldUpdateData): Promise<VaultYieldUpdateResponse> {
    return apiClient.post<VaultYieldUpdateResponse>(`${VAULTS_BASE_URL}${id}/update-yield/`, data);
  }

  // Vault Transactions
  async getTransactions(vaultId: number, type?: string): Promise<VaultTransaction[]> {
    let url = `${VAULTS_BASE_URL}${vaultId}/transactions/`;
    if (type) {
      url += `?type=${type}`;
    }
    const response = await apiClient.get<PaginatedResponse<VaultTransaction>>(url);
    return response.results;
  }

  async getAllTransactions(params?: { vault?: number; type?: string }): Promise<VaultTransaction[]> {
    let url = TRANSACTIONS_BASE_URL;
    const searchParams = new URLSearchParams();

    if (params?.vault) {
      searchParams.append('vault', params.vault.toString());
    }
    if (params?.type) {
      searchParams.append('type', params.type);
    }

    if (searchParams.toString()) {
      url += `?${searchParams.toString()}`;
    }

    const response = await apiClient.get<PaginatedResponse<VaultTransaction>>(url);
    return response.results;
  }

  // Transaction Update/Delete
  async updateTransaction(id: number, data: VaultTransactionUpdateData): Promise<VaultTransactionUpdateResponse> {
    return apiClient.patch<VaultTransactionUpdateResponse>(`${TRANSACTIONS_BASE_URL}${id}/`, data);
  }

  async deleteTransaction(id: number): Promise<VaultTransactionDeleteResponse> {
    return apiClient.delete<VaultTransactionDeleteResponse>(`${TRANSACTIONS_BASE_URL}${id}/`);
  }
}

class FinancialGoalsService {
  // ==================== FINANCIAL GOALS ====================

  async getAll(params?: {
    is_active?: boolean;
    is_completed?: boolean;
    category?: string;
  }): Promise<FinancialGoalListItem[]> {
    let url = GOALS_BASE_URL;
    const searchParams = new URLSearchParams();

    if (params?.is_active !== undefined) {
      searchParams.append('is_active', params.is_active.toString());
    }
    if (params?.is_completed !== undefined) {
      searchParams.append('is_completed', params.is_completed.toString());
    }
    if (params?.category) {
      searchParams.append('category', params.category);
    }

    if (searchParams.toString()) {
      url += `?${searchParams.toString()}`;
    }

    const response = await apiClient.get<PaginatedResponse<FinancialGoalListItem>>(url);
    return response.results;
  }

  async getById(id: number): Promise<FinancialGoal> {
    return apiClient.get<FinancialGoal>(`${GOALS_BASE_URL}${id}/`);
  }

  async create(data: FinancialGoalFormData): Promise<FinancialGoal> {
    return apiClient.post<FinancialGoal>(GOALS_BASE_URL, data);
  }

  async update(id: number, data: Partial<FinancialGoalFormData>): Promise<FinancialGoal> {
    return apiClient.put<FinancialGoal>(`${GOALS_BASE_URL}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${GOALS_BASE_URL}${id}/`);
  }

  // Goal Operations
  async checkCompletion(id: number): Promise<FinancialGoalCheckResponse> {
    return apiClient.post<FinancialGoalCheckResponse>(`${GOALS_BASE_URL}${id}/check-completion/`, {});
  }

  async addVaults(id: number, vaultIds: number[]): Promise<FinancialGoalVaultsResponse> {
    const data: FinancialGoalVaultsRequest = { vault_ids: vaultIds };
    return apiClient.post<FinancialGoalVaultsResponse>(`${GOALS_BASE_URL}${id}/add-vaults/`, data);
  }

  async removeVaults(id: number, vaultIds: number[]): Promise<FinancialGoalVaultsResponse> {
    const data: FinancialGoalVaultsRequest = { vault_ids: vaultIds };
    return apiClient.post<FinancialGoalVaultsResponse>(`${GOALS_BASE_URL}${id}/remove-vaults/`, data);
  }
}

export const vaultsService = new VaultsService();
export const financialGoalsService = new FinancialGoalsService();
