/**
 * Funções Auxiliares
 *
 * Funções utilitárias para cálculos, manipulação de arrays e outras operações comuns.
 */

import { translate } from '@/config/constants';

/**
 * Traduz categoria de despesa ou receita de forma conveniente
 *
 * @param category - Categoria em inglês
 * @param type - Tipo ('expense' ou 'revenue')
 * @returns Categoria traduzida em português
 *
 * @example
 * translateCategory('food and drink', 'expense') // "Comida e Bebida"
 * translateCategory('salary', 'revenue') // "Salário"
 */
export const translateCategory = (
  category: string,
  type: 'expense' | 'revenue'
): string => {
  const categoryKey = type === 'expense' ? 'expenseCategories' : 'revenueCategories';
  return translate(categoryKey, category);
};

/**
 * Agrupa array por propriedade
 *
 * @param array - Array a ser agrupado
 * @param property - Propriedade para agrupar
 * @returns Objeto com arrays agrupados por valor da propriedade
 *
 * @example
 * groupByProperty([{status: 'pending', value: 100}, {status: 'paid', value: 200}, {status: 'pending', value: 50}], 'status')
 * // { pending: [{...}, {...}], paid: [{...}] }
 */
export const groupByProperty = <T>(
  array: T[],
  property: keyof T
): Record<string, T[]> => {
  return array.reduce((acc, item) => {
    const key = String(item[property]);
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(item);
    return acc;
  }, {} as Record<string, T[]>);
};

/**
 * Calcula percentual
 *
 * @param value - Valor parcial
 * @param total - Valor total
 * @returns Percentual (0-100)
 *
 * @example
 * calculatePercentage(25, 100) // 25
 * calculatePercentage(0, 100) // 0
 * calculatePercentage(50, 0) // 0 (evita divisão por zero)
 */
export const calculatePercentage = (value: number, total: number): number => {
  if (total === 0) return 0;
  return (value / total) * 100;
};

/**
 * Soma valores de uma propriedade em um array
 *
 * @param array - Array de objetos
 * @param property - Propriedade numérica a somar
 * @returns Soma total
 *
 * @example
 * sumByProperty([{value: 100}, {value: 200}, {value: 50}], 'value') // 350
 */
export const sumByProperty = <T>(array: T[], property: keyof T): number => {
  return array.reduce((sum, item) => {
    const value = item[property];
    return sum + (typeof value === 'number' ? value : parseFloat(String(value)) || 0);
  }, 0);
};

/**
 * Filtra valores únicos de um array
 *
 * @param array - Array com possíveis duplicatas
 * @returns Array sem duplicatas
 *
 * @example
 * unique([1, 2, 2, 3, 3, 3]) // [1, 2, 3]
 * unique(['a', 'b', 'a']) // ['a', 'b']
 */
export const unique = <T>(array: T[]): T[] => {
  return Array.from(new Set(array));
};

/**
 * Ordena array por propriedade
 *
 * @param array - Array a ser ordenado
 * @param property - Propriedade para ordenar
 * @param direction - Direção ('asc' ou 'desc')
 * @returns Array ordenado
 *
 * @example
 * sortByProperty([{value: 300}, {value: 100}, {value: 200}], 'value', 'asc')
 * // [{value: 100}, {value: 200}, {value: 300}]
 */
export const sortByProperty = <T>(
  array: T[],
  property: keyof T,
  direction: 'asc' | 'desc' = 'asc'
): T[] => {
  return [...array].sort((a, b) => {
    const aVal = a[property];
    const bVal = b[property];

    if (aVal < bVal) return direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    return 0;
  });
};

/**
 * Valida CPF
 *
 * @param cpf - CPF a ser validado (com ou sem formatação)
 * @returns true se CPF é válido
 *
 * @example
 * isValidCPF('123.456.789-09') // true ou false
 * isValidCPF('12345678909') // true ou false
 */
export const isValidCPF = (cpf: string): boolean => {
  const cleaned = cpf.replace(/\D/g, '');

  if (cleaned.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(cleaned)) return false; // Rejeita números repetidos

  let sum = 0;
  let remainder;

  // Valida primeiro dígito verificador
  for (let i = 1; i <= 9; i++) {
    sum += parseInt(cleaned.substring(i - 1, i)) * (11 - i);
  }
  remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(cleaned.substring(9, 10))) return false;

  sum = 0;
  // Valida segundo dígito verificador
  for (let i = 1; i <= 10; i++) {
    sum += parseInt(cleaned.substring(i - 1, i)) * (12 - i);
  }
  remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(cleaned.substring(10, 11))) return false;

  return true;
};

/**
 * Trunca texto com reticências
 *
 * @param text - Texto a truncar
 * @param maxLength - Comprimento máximo
 * @returns Texto truncado
 *
 * @example
 * truncate('Este é um texto muito longo', 10) // "Este é um..."
 */
export const truncate = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
};

/**
 * Debounce function - atrasa execução de função até que pare de ser chamada
 *
 * @param func - Função a ser executada
 * @param delay - Atraso em ms
 * @returns Função com debounce
 *
 * @example
 * const debouncedSearch = debounce((query) => searchAPI(query), 300);
 * debouncedSearch('termo'); // Só executa após 300ms sem novas chamadas
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: ReturnType<typeof setTimeout>;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

/**
 * Retorna cor de badge para módulo do sistema
 *
 * @param module - Nome do módulo ('finance', 'security', 'library')
 * @returns Classe CSS do Tailwind para cor do badge
 *
 * @example
 * getModuleBadgeColor('finance') // 'bg-green-500'
 */
export const getModuleBadgeColor = (module: string): string => {
  switch (module) {
    case 'finance':
      return 'bg-green-500';
    case 'security':
      return 'bg-blue-500';
    case 'library':
      return 'bg-purple-500';
    default:
      return 'bg-gray-500';
  }
};

/**
 * Retorna label traduzido para módulo do sistema
 *
 * @param module - Nome do módulo em inglês
 * @returns Label em português
 *
 * @example
 * getModuleLabel('finance') // 'Finanças'
 */
export const getModuleLabel = (module: string): string => {
  switch (module) {
    case 'finance':
      return 'Finanças';
    case 'security':
      return 'Segurança';
    case 'library':
      return 'Biblioteca';
    default:
      return module;
  }
};

/**
 * Retorna label traduzido para tipo de entidade
 *
 * @param type - Tipo de entidade em inglês
 * @returns Label em português
 *
 * @example
 * getEntityLabel('expense') // 'Despesa'
 */
export const getEntityLabel = (type: string): string => {
  const labels: Record<string, string> = {
    expense: 'Despesa',
    revenue: 'Receita',
    account: 'Conta',
    password: 'Senha',
    archive: 'Arquivo',
    book: 'Livro',
    summary: 'Resumo',
    transfer: 'Transferência',
    credit_card: 'Cartão de Crédito',
    loan: 'Empréstimo',
    author: 'Autor',
    publisher: 'Editora',
    reading: 'Leitura',
  };
  return labels[type] || type;
};
