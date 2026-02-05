import { apiClient } from './api-client';
import { API_CONFIG } from '@/config/constants';
import type { CreditCardBill, CreditCardBillFormData, BillPaymentFormData, BillPaymentResponse, PaginatedResponse, BillItemsResponse } from '@/types';

class CreditCardBillsService {
  async getAll(params?: Record<string, any>): Promise<CreditCardBill[]> {
    const response = await apiClient.get<PaginatedResponse<CreditCardBill>>(API_CONFIG.ENDPOINTS.CREDIT_CARD_BILLS, params);
    return response.results;
  }

  async getById(id: number): Promise<CreditCardBill> {
    return apiClient.get<CreditCardBill>(`${API_CONFIG.ENDPOINTS.CREDIT_CARD_BILLS}${id}/`);
  }

  async create(data: CreditCardBillFormData): Promise<CreditCardBill> {
    return apiClient.post<CreditCardBill>(API_CONFIG.ENDPOINTS.CREDIT_CARD_BILLS, data);
  }

  async update(id: number, data: Partial<CreditCardBillFormData>): Promise<CreditCardBill> {
    return apiClient.put<CreditCardBill>(`${API_CONFIG.ENDPOINTS.CREDIT_CARD_BILLS}${id}/`, data);
  }

  async delete(id: number): Promise<void> {
    return apiClient.delete(`${API_CONFIG.ENDPOINTS.CREDIT_CARD_BILLS}${id}/`);
  }

  async getByCard(cardId: number): Promise<CreditCardBill[]> {
    return this.getAll({ credit_card: cardId });
  }

  async getByStatus(status: 'open' | 'closed' | 'paid' | 'overdue'): Promise<CreditCardBill[]> {
    return this.getAll({ status });
  }

  async getByYear(year: string): Promise<CreditCardBill[]> {
    return this.getAll({ year });
  }

  async payBill(billId: number, data: BillPaymentFormData): Promise<BillPaymentResponse> {
    return apiClient.post<BillPaymentResponse>(`${API_CONFIG.ENDPOINTS.CREDIT_CARD_BILLS}${billId}/pay/`, data);
  }

  async reopenBill(billId: number): Promise<{ message: string; bill: CreditCardBill }> {
    return apiClient.post<{ message: string; bill: CreditCardBill }>(`${API_CONFIG.ENDPOINTS.CREDIT_CARD_BILLS}${billId}/reopen/`, {});
  }

  /**
   * Busca todos os itens de uma fatura (despesas legadas + parcelas).
   * Este método retorna uma lista unificada de todos os lançamentos da fatura,
   * incluindo despesas fixas (CreditCardExpense) e parcelas de compras (CreditCardInstallment).
   */
  async getBillItems(billId: number): Promise<BillItemsResponse> {
    return apiClient.get<BillItemsResponse>(`${API_CONFIG.ENDPOINTS.CREDIT_CARD_BILLS}${billId}/items/`);
  }
}

export const creditCardBillsService = new CreditCardBillsService();
