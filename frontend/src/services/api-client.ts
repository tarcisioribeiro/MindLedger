import axios, { type AxiosInstance, AxiosError, type InternalAxiosRequestConfig } from 'axios';
import Cookies from 'js-cookie';
import { API_CONFIG } from '@/config/constants';

// ============================================================================
// Types
// ============================================================================

/**
 * Formato de resposta de erro do Django REST Framework.
 */
interface DRFErrorResponse {
  detail?: string;
  [field: string]: string | string[] | undefined;
}

/**
 * Tipo para dados de requisicao (body).
 * Aceita objetos, FormData, ou valores primitivos.
 */
type RequestData = Record<string, unknown> | FormData | null | undefined;

/**
 * Tipo para parametros de query string.
 */
type QueryParams = Record<string, string | number | boolean | string[] | number[] | undefined>;

// ============================================================================
// Custom Error Classes
// ============================================================================

export class AuthenticationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends Error {
  errors: Record<string, string[]>;

  constructor(message: string, errors: Record<string, string[]> = {}) {
    super(message);
    this.name = 'ValidationError';
    this.errors = errors;
  }
}

export class NotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NotFoundError';
  }
}

export class PermissionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'PermissionError';
  }
}

// ============================================================================
// API Client
// ============================================================================

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: Array<() => void> = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Importante: permite enviar cookies httpOnly
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - Os tokens são enviados automaticamente como httpOnly cookies
    // Não precisamos adicionar Authorization header manualmente
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        console.log('[ApiClient] Request to', config.url, '(tokens enviados via httpOnly cookies)');

        // Se o data é FormData, remove o Content-Type para que o axios defina automaticamente
        // o multipart/form-data com o boundary correto
        if (config.data instanceof FormData) {
          if (config.headers) {
            delete config.headers['Content-Type'];
          }
        }

        return config;
      },
      (error: unknown) => Promise.reject(error)
    );

    // Response interceptor - Handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean;
        };

        // NÃO tenta refresh para endpoints de autenticação
        const authEndpoints = [
          API_CONFIG.ENDPOINTS.LOGIN,
          API_CONFIG.ENDPOINTS.REFRESH_TOKEN,
          API_CONFIG.ENDPOINTS.VERIFY_TOKEN,
          API_CONFIG.ENDPOINTS.REGISTER,
        ];

        const isAuthEndpoint = authEndpoints.some(endpoint =>
          originalRequest.url?.includes(endpoint)
        );

        // If error is 401 and we haven't retried yet and NOT an auth endpoint
        if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
          if (this.isRefreshing) {
            // Wait for refresh to complete
            return new Promise((resolve) => {
              this.refreshSubscribers.push(() => {
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            console.log('[ApiClient] Attempting token refresh via httpOnly cookie');

            // O refresh token já está no cookie httpOnly
            // O backend vai lê-lo automaticamente
            await axios.post(
              `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.REFRESH_TOKEN}`,
              {}, // Body vazio - o backend lê o refresh_token do cookie
              { withCredentials: true } // Envia cookies
            );

            console.log('[ApiClient] Token refreshed successfully');

            // Notify all waiting requests
            this.refreshSubscribers.forEach((callback) => callback());
            this.refreshSubscribers = [];

            return this.client(originalRequest);
          } catch (refreshError) {
            console.error('[ApiClient] Token refresh failed:', refreshError);
            this.clearTokens();
            // Não redireciona aqui - deixa o erro ser tratado normalmente
            return Promise.reject(new AuthenticationError('Sua sessão expirou. Por favor, faça login novamente.'));
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  /**
   * Formata mensagem de erro do Django REST Framework.
   */
  private formatErrorMessage(data: unknown): string {
    if (typeof data === 'string') {
      return data;
    }

    if (data && typeof data === 'object') {
      const errorData = data as DRFErrorResponse;

      if (errorData.detail) {
        return errorData.detail;
      }

      // Handle Django REST Framework validation errors
      const errorMessages: string[] = [];

      for (const [field, errors] of Object.entries(errorData)) {
        if (Array.isArray(errors)) {
          errorMessages.push(`${field}: ${errors.join(', ')}`);
        } else if (typeof errors === 'string') {
          errorMessages.push(`${field}: ${errors}`);
        }
      }

      if (errorMessages.length > 0) {
        return errorMessages.join('\n');
      }
    }

    return 'Ocorreu um erro desconhecido';
  }

  private handleError(error: AxiosError): Error {
    const response = error.response;

    if (!response) {
      return new Error('Erro de rede. Por favor, verifique sua conexão.');
    }

    const data = response.data as unknown;

    switch (response.status) {
      case 400: {
        const errorData = data as Record<string, string[]> | undefined;
        return new ValidationError(
          this.formatErrorMessage(data) || 'Erro de validação',
          errorData && typeof errorData === 'object' && !('detail' in errorData)
            ? errorData
            : {}
        );
      }
      case 401:
        return new AuthenticationError(
          this.formatErrorMessage(data) || 'Falha na autenticação'
        );
      case 403:
        return new PermissionError(
          this.formatErrorMessage(data) || 'Você não tem permissão para realizar esta ação'
        );
      case 404:
        return new NotFoundError(
          this.formatErrorMessage(data) || 'Recurso não encontrado'
        );
      case 500:
        return new Error(
          this.formatErrorMessage(data) || 'Erro interno do servidor. Por favor, tente novamente mais tarde.'
        );
      default:
        return new Error(
          this.formatErrorMessage(data) || `Ocorreu um erro (${response.status})`
        );
    }
  }

  // ============================================================================
  // Token Management
  // ============================================================================

  // NOTA: Os tokens access_token e refresh_token são httpOnly cookies
  // gerenciados pelo backend. Não podemos (e não devemos) acessá-los via JavaScript.
  // Eles são enviados automaticamente pelo navegador em cada requisição.

  private tokenValidationCache: { isValid: boolean; timestamp: number } | null = null;
  private readonly CACHE_DURATION = 5000; // 5 segundos

  public clearTokens() {
    // Limpa apenas os cookies que NÃO são httpOnly (user_data, user_permissions)
    // Os httpOnly cookies (access_token, refresh_token) são removidos pelo backend no logout
    Cookies.remove('user_data');
    Cookies.remove('user_permissions');
    // Limpa o cache de validação
    this.tokenValidationCache = null;
  }

  public async hasValidToken(): Promise<boolean> {
    // Usa cache se disponível e recente (menos de 5 segundos)
    if (this.tokenValidationCache) {
      const age = Date.now() - this.tokenValidationCache.timestamp;
      if (age < this.CACHE_DURATION) {
        console.log('[ApiClient] Using cached token validation:', this.tokenValidationCache.isValid);
        return this.tokenValidationCache.isValid;
      }
    }

    // Verifica se há um token válido fazendo uma chamada ao endpoint de verify
    try {
      await this.client.post(API_CONFIG.ENDPOINTS.VERIFY_TOKEN);
      this.tokenValidationCache = { isValid: true, timestamp: Date.now() };
      return true;
    } catch {
      this.tokenValidationCache = { isValid: false, timestamp: Date.now() };
      return false;
    }
  }

  // ============================================================================
  // HTTP Methods
  // ============================================================================

  async get<T>(url: string, params?: QueryParams): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: RequestData): Promise<T> {
    if (import.meta.env.DEV) {
      console.log('POST Request:', { url, data });
    }
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: RequestData): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  async patch<T>(url: string, data?: RequestData): Promise<T> {
    const response = await this.client.patch<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
